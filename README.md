
# USB_Dropbox_Greeter
Simple Python Code that will synchronize the Dropbox folder from my USB stick as soon as I insert it to my PC.
Feel free to use, some settings can be configured in config.py
## How To Use
#### 1. Install Dropbox for Python
```
pip install dropbox
```
#### 2. Place your API key in config.py
```python
#Place yoyr OAuth2 Dropbox access token here
TOKEN = "TOKEN STRING"
```
You can generate the Dropbox Access token in the App Console.
See: https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/

#### 3. Run Script
```
python main.py
```

