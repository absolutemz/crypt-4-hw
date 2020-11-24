import sys

import ecdsa
import ipfshttpclient


def generate_keys():

    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key()

    return private_key, public_key


def ipfs_link_generating(user_name, user_info, filename_pub_key):
    filename = f'{user_name}_{filename_pub_key[:8]}'
    user_file = open(f'{filename}', "w")

    # Запись пользовательских данных в файл
    user_file.write(f'Name: {user_name}\n')
    user_file.write(f'Information: {user_info}')
    user_file.close()

    client = ipfshttpclient.connect()
    res = client.add(f'{filename}')

    ipfs_link = res["Hash"]
    ipfs_link_sign = vasya_pr_key.sign(ipfs_link.encode("utf-8"))  # генерация подписи

    return ipfs_link, ipfs_link_sign.hex()


def file_updating(user_pubkey, user_ipfs_link):
    """Запись/обновление ipfs-link пользователя в файле name_service.txt"""

    updating = False  # обновление/новая запись
    with open('name_service.txt') as f:
        for line in f:
            if line.find(user_pubkey) != -1:
                updating = True
                break
    f.close()
    if not updating:  # новая запись в name-сервис
        our_data_file = open("name_service.txt", "a")
        our_data_file.write(f'\n{user_pubkey}')
        our_data_file.write(f'\nlink:{user_ipfs_link}')
        our_data_file.close()
    else:
        file_str = ""
        with open ('name_service.txt', 'w+') as f:  # update старой записи
            for line in f:
                if line.find(user_pubkey) == -1:
                    file_str += line
        f.close()
        our_data_file = open("name_service.txt", "w")
        our_data_file.write(file_str)
        our_data_file.close()

        our_data_file = open("name_service.txt", "a")
        our_data_file.write(f'\n{user_pubkey}')
        our_data_file.write(f'\nlink:{user_ipfs_link}')
        our_data_file.close()


def name_service_set(user_identify, ipfs_link, link_sign):
    pub_key_from_identify = user_identify.split(':')[1]
    user_pub_key = "".join(pub_key_from_identify)
    verifying_key = ecdsa.VerifyingKey.from_string(bytes.fromhex(user_pub_key), curve=ecdsa.SECP256k1)
    try:
        verifying_key.verify(bytes.fromhex(link_sign), bytes(ipfs_link, encoding="utf-8"))
    except ecdsa.keys.BadSignatureError:
        print("Wrong digital signature!\n")
    else:
        file_updating(user_identify, ipfs_link)
        print("\nresult: ok (signature correct)\n")


def name_service_get(username):
    """Возвращает ipfs-link пользователя и data из ipfs, если он найден"""

    user_found = False
    with open('name_service.txt') as f:
        for line in f:
            if user_found == False:
                if line.strip('\n') == username:
                    user_found = True
            if user_found:
                if line.find("link") != -1:
                    ipfs_link = line
                    break
    if user_found:
        print(f'\n{ipfs_link}\n')  # возвращает ipfs-link
        print('data(from IPFS node):')
        ipfs_link = ipfs_link[ipfs_link.find(':')+1:]
        client = ipfshttpclient.connect()
        data_from_ipfs = client.cat(ipfs_link).decode('utf8')
        print(data_from_ipfs)
    else:
        print("\nuser not found\n")


if __name__ == '__main__':
    if sys.argv[1] == "--request-type=name-record-generate":
        command = "generate"
    elif sys.argv[1] == "--request-type=name-record-set":
        uid = sys.argv[2]
        ipfs_link = sys.argv[3]
        sig = sys.argv[4]
        command = "set"
    elif sys.argv[1] == "--request-type=name-record-get":
        uid = sys.argv[2]
        command = "get"

    if command == "generate":
        vasya_pr_key, vasya_pub_key = generate_keys()  # генерация ключей secp256k1
        pr_key_str = vasya_pr_key.to_string()
        pub_key_str = vasya_pub_key.to_string()

        pub_key_str_to_file = pub_key_str.hex()
        name = str(input("Username: "))
        birthdate = str(input("Information: "))
        ipfs_link, ipfs_link_sig = ipfs_link_generating(name, birthdate, pub_key_str_to_file)

        name_service_username = f'{name}:{pub_key_str.hex()}'

        print(f'--uid={name_service_username}\n--ipfs-link={ipfs_link}\n--sig={ipfs_link_sig}')

    if command == "set":
        # Обрезаем параметры командной строки начиная с '='
        uid = uid[uid.find('=')+1:]
        ipfs_link = ipfs_link[ipfs_link.find('=')+1:]
        sig = sig[sig.find('=')+1:]

        name_service_set(uid, ipfs_link, sig)

    if command == "get":
        uid = uid[uid.find('=') + 1:]
        name_service_get(uid)
