import os
import secrets
import base64
from PIL import Image
from hashter import db
from flask import current_app
from Cryptodome.Cipher import AES
from Cryptodome import Random
from Cryptodome.Hash import SHA256
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Random import get_random_bytes


def randomName(name):
	name_key = get_random_bytes(16)
	encrypted_name = base64.b64encode(encryptAES_CBC(name_key, name)).decode('utf-8')
	return encrypted_name

def save_post_picture(form_picture):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_fn = random_hex + f_ext
	picture_path = os.path.join(current_app.root_path, 'static/post_pics', picture_fn)
	output_size = (300,300)
	i = Image.open(form_picture)
	i.thumbnail(output_size)
	i.save(picture_path)
	return picture_fn

def save_encrypted_post_picture(key, form_picture):
	chunksize = 64*1024
	IV = get_random_bytes(16)
	encryptor = AES.new(key, AES.MODE_CBC, IV)
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_fn = random_hex + f_ext
	temp_picture_path = os.path.join(current_app.root_path, 'static/post_pics/temp.jpg')
	picture_path = os.path.join(current_app.root_path, 'static/post_pics', picture_fn)
	output_size = (300,300)
	i = Image.open(form_picture)
	i.thumbnail(output_size)
	i.save(temp_picture_path)
	with open(temp_picture_path, 'rb') as infile:
		with open(picture_path, "wb") as outfile:
			outfile.write(IV)
			while True:
				chunk = infile.read(chunksize)
				if len(chunk) == 0:
					break
				elif len(chunk)%16 != 0:
					chunk += b" " * (16 - (len(chunk)%16))
				outfile.write(encryptor.encrypt(chunk))
				os.remove(os.path.join(current_app.root_path, 'static/post_pics/temp.jpg'))
	return picture_fn

def decrypt_picture(key, filename):
    chunksize = 64*1024
    outputFile = "temp" + filename
    picture_path = os.path.join(current_app.root_path, 'static/post_pics', filename)
    new_picture_path = os.path.join(current_app.root_path, 'static/post_pics', outputFile)
    print("HEEEEEEEEEEEEEERE", picture_path)
    with open(picture_path, 'rb') as infile:
        IV = infile.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, IV)

        with open(new_picture_path, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)

                if len(chunk) == 0:
                    break
               	outfile.write(decryptor.decrypt(chunk))
    return outputFile

def get_key(password):
	hasher = SHA256.new(password.encode('utf-8'))
	return hasher.digest()	

def encryptAES_CBC(key, plaintext):
	plaintext = plaintext.encode('utf-8')
	padded_text = pad(plaintext, AES.block_size)
	IV = Random.new().read(16)
	encryptor = AES.new(key, AES.MODE_CBC, IV)
	ciphertext = encryptor.encrypt(padded_text)
	message = IV+ciphertext
	return(message)


def decryptAES_CBC(key, ciphertext):
	IV = ciphertext[0:16]
	new_ciphertext = ciphertext[16:len(ciphertext)]
	decryptor = AES.new(key, AES.MODE_CBC, IV)
	return unpad(decryptor.decrypt(new_ciphertext), AES.block_size)