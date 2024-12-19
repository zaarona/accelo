import pandas as pd
import requests

response = requests.get('http://localhost:5253/api/tests/test/1.0.0')
print(response.json())
