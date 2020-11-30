# Census-TigerWeb-Wrapper

```python
from tigerweb import TigerWeb

subject = TigerWeb([[-71.799502, 42.585699]], return_geometry=False)
cbsa_dict = subject.get_cbsa()[0]

cbsa = TigerWeb(geometry=cbsa_dict["geometry"]["coordinates"], geometry_type=cbsa_dict["geometry"]["type"])
counties = cbsa.get_counties(within_polygon=True)
```
