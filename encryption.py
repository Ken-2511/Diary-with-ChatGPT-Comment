import base64


def encrypt(data: str):
    data = data.encode('utf-8')
    encoded_bytes = base64.b64encode(data)
    encoded_string = encoded_bytes.decode('utf-8')
    return encoded_string


def encrypt_secret_recursive(data: str):
    # find `<secret>`
    start = data.find('<secret>')
    end = data.find('</secret>')
    if start == -1:
        return data
    # extract the secret
    secret = data[start + len('<secret>'):end]
    # encrypt the secret
    encrypted_secret = encrypt(secret)
    # if we found the end, extract the rest of data
    if end != -1:
        rest = data[end + len('</secret>'):]
        return data[:start] + '<secret>\n' + encrypted_secret + '\n</secret>' + encrypt_secret_recursive(rest)
    return data[:start] + '<secret>\n' + encrypted_secret + '\n</secret>'

if __name__ == '__main__':
    data = '<secret>hello world</secret> test <secret> fasdfg'
    encrypted_data = encrypt_secret_recursive(data)
    print(encrypted_data)