
import sys
sys.path.insert(0, 'src')
from openmetaphysics.agents.bazi_explainer import BaziExplainer
from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.core.schemas import Gender, GeoPoint
from datetime import datetime
from zoneinfo import ZoneInfo

agent = BaziAgent()
inp = BaziInput(
    request_id='test-explainer',
    born_at=datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo('Asia/Shanghai')),
    gender=Gender.MALE,
    born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone='Asia/Shanghai'),
)
output = agent.compute(inp)

explainer = BaziExplainer(provider=None)
text = explainer.render(output)
print(text)

pattern_info = explainer._get_pattern_info(output.result)
print()
print('Pattern Info:')
print(pattern_info)
print()
print('Expected:')
print('  month_earthly_branch: 申')
print('  dominant_hidden: 庚')
print('  pattern_ten_god: 正官 (for 乙日主)')

