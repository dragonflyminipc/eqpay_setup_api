from bitcoin import Bitcoin

client = Bitcoin("http://rpcuser:rpcpassword@211.216.3.196:9999")

# result = client.make_request("getpeerinfo", [])
# print(str(round(result["result"][0]["synced_blocks"]/result["result"][0]["startingheight"]*100, 4))+"%")

result = client.make_request("getwalletinfo", [])
print(result)