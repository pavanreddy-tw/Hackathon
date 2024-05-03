from hackathon.csp import CSPBase
from hackathon.embeddings import OpenAIEmbeddings
from hackathon.stt import OpenAISTT
from hackathon.chat import OpenAIChat

from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, ComplexField, SimpleField, SearchableField, SearchFieldDataType
)



import os
import json
import asyncio
import aiofiles
import requests

from dotenv import load_dotenv
load_dotenv()

class AzureCSP(CSPBase):
    def __init__(self, embeddings=None, chat=None, stt=None, *args, **kwargs):
        super().__init__()

        if embeddings == 'openai' or embeddings is None:
            if embeddings is None: print("No embeddings client provided. Setting Default: OpenAI")
            self.embeddings_client = OpenAIEmbeddings(kwargs.get('openai_api_key', None))
        else:
            raise NotImplemented(f"Embedding Client {embeddings} not Implemented")

        if stt == 'openai' or stt is None:
            if stt is None: print("No stt client provided. Setting Default: OpenAI")
            self.stt_client = OpenAISTT(kwargs.get('openai_api_key', None))
        else:
            raise NotImplemented(f"STT Client {stt} not Implemented")
        
        if chat == 'openai' or chat is None:
            if chat is None: print("No chat client provided. Setting Default: OpenAI")
            self.chat_client = OpenAIChat(kwargs.get('openai_api_key', None))
        else:
            raise NotImplemented(f"Chat Client {chat} not Implemented")

        #Requires correct key to initialize server
        # search_credential = AzureKeyCredential(os.getenv("AZURE_KEY"))
        # self.index_client = SearchIndexClient(endpoint=os.getenv("AZURE_ENDPOINT"), credential=search_credential)


    async def index_data(self, index_name, file_path):
        search_client = self.index_client.get_search_client(index_name)
        search_index = SearchIndex(name=index_name)

        if index_name == "alcohol":
            search_index = SearchIndex(
                name=index_name,
                fields=[
                    SimpleField(name="ID", type=SearchFieldDataType.String, key=True),
                    SearchableField(name="Category", type=SearchFieldDataType.String, filterable=True, sortable=True,
                                    facetable=True),
                    SearchableField(name="Title", type=SearchFieldDataType.String, searchable=True),
                    SearchableField(name="Content", type=SearchFieldDataType.String, searchable=True),
                    SimpleField(name="Severity", type=SearchFieldDataType.Int32, filterable=True, sortable=True,
                                facetable=True),
                    ComplexField(name="Title_Vector",
                                 type=SearchFieldDataType.Collection(SearchFieldDataType.Double)),
                    ComplexField(name="Content_Vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Double))
                ]
            )

        self.index_client.create_or_update_index(search_index)

        with open(file_path, 'r') as f:
            input_documents = json.load(f) or []

        sample_documents = await self._get_sample_documents(input_documents, index_name)

        batch_size = 100
        for i in range(0, len(sample_documents), batch_size):
            batch = sample_documents[i:i + batch_size]
            await search_client.upload_documents(documents=batch)

        return "Successfully Indexed Data"


    async def simple_hs(self, prompt, index_name):
        search_client = self.index_client.get_search_client(index_name)
        query_embeddings = await self.embeddings_client.get_embeddings(prompt)

        search_options = {
            'search_fields': 'Title,Content',
            'select': 'ID,Category,Title,Content,Severity',
            'top': 3,
            'filter': '',
            'queryType': 'full',
            'scoringProfile': '',
        }

        if index_name == 'alcohol':
            search_options['select'] = 'ID,Category,Title,Content,Severity'
        else:
            raise KeyError(f"{index_name} does not exist")

        response = await search_client.search(query=query_embeddings, **search_options)

        response_holder = []
        async for result in response.results:
            search_result = {
                "images": ", ".join(result.document['Images']),
                "category": result.document.get('Category', 'N/A'),
                "pdf": result.document.get('PDF', ''),
                "content": result.document['Content'],
                "score": result.score
            }

            response_holder.append(search_result)

        response_holder_total = len(response_holder)

        return response_holder, response_holder_total


    async def start_conversation(self, prompt, type):
         
        category = self._get_category(prompt)

        if category.casefold() == 'none':
            return self._process_out_of_category()

        category = category.split(",")

        if len(category) > 1:
            return self._narrow_category()
        
        if category == 'GET RESOURCES':
            location = self._get_location_from_response()
            if location is None:
                return self._request_location()
            self._return_resources(location)

        response_holder, response_holder_total = self.simple_hs(prompt, category)

        final_prompt = self._create_context(response_holder, response_holder_total)

        return self._get_response(final_prompt)
    



    def _get_category(self, prompt):
        pass

    def _process_out_of_category(self, prompt):
        pass

    def _narrow_category(self, prompt):
        pass

    def _create_context(self, response_holder, category):
        pass

    def _return_resources(self, locations):
        pass

    def _request_location(self):
        pass

    def _get_location_from_response(self, locations):
        pass

    def _get_response(self, prompt):
        return self.chat_client.get_response(prompt)


    async def speech_to_text(self, audio_data):
        return self.stt_client.get_text(audio_data)


    async def _get_sample_documents(self, documents):
        sample_documents = []
        failed_ids = []

        for document in documents:
            try:
                content = document.get("Content", "")
                title = document.get("Title", "")

                content_embeddings = await self.embeddings_client.get_embeddings(content)
                title_embeddings = await self.embeddings_client.get_embeddings(title)

                document["Title_Vector"] = title_embeddings
                document["Content_Vector"] = content_embeddings

                sample_documents.append(document)
            except Exception as ex:
                question_id = document.get("Id", "Unknown")
                failed_ids.append(question_id)
                print(f"Error processing document ID {question_id}: {ex}")

        if failed_ids:
            async with aiofiles.open('failedIds.txt', 'w') as f:
                await f.write('\n'.join(failed_ids))

        return sample_documents

