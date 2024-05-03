import os
from hackathon.csp import GCPCSP

import sys
sys.path.append("C:\\Users\\Pavan Reddy\\Desktop\\Hackathon")

gcpscp = GCPCSP(embeddings='gcp', chat='gcp', stt='gcp')

# file_path = "gs://hackathon-12341/hackathon/index.json"
file_path = "..\..\Data"


# print(gcpscp.index_data(project_id='hallowed-air-418016', file_path=file_path))

# print(gcpscp.simple_hs("My friend is hiding his drinking habits", index_name='warning_signs', project_id='hallowed-air-

print(gcpscp.chat_client.get_response("Hello!")[0])