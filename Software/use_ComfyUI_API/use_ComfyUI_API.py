import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
from PIL import Image
import base64
import random


server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())
IMAGE_PATH = "test.jpg"
WORKFLOW_JSON_PATH = "img2img.json"

def get_imh2img_prompt(image_path, workflow_json_path):
    try:
        # 读取图像并编码为 base64
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        # 读取工作流 JSON
        with open(workflow_json_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        # 修改workflow JSON，修改上传图片的路径为将要保存的临时图片文件路径
        workflow["10"]["inputs"]["image"] = "D:/Repos/SheepPainter/Software/use_ComfyUI_API/temp_image.png"

        workflow["3"]["inputs"]["seed"] = random.randint(0, 0xffffffffffffffff)
        # 将图片保存为ComfyUI可以读取的临时文件
        with open("D:/Repos/SheepPainter/Software/use_ComfyUI_API/temp_image.png", "wb") as f:
            f.write(base64.b64decode(encoded_string))
        return workflow
    except Exception as e:
        print(f"发生错误：{e}")


def queue_prompt(prompt):
    """
    将包含提示信息和客户端ID的JSON数据通过HTTP POST请求发送到ComfyUI服务器
    """
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    """
    基于关于图像位置的详细信息和服务器地址构建URL，然后从服务器检索并返回原始图像数据
    """
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    """从
    服务器检索与特定prompt_id关联的历史记录，并将数据作为 Python 对象返回
    """
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    """
    使用 WebSocket 连接 (ws) 向服务器发送提示 (prompt)，并接收服务器生成的图像数据。
    """
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    current_node = ""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break #Execution is done
                    else:
                        current_node = data['node']
        else:
            if current_node == "save_image_websocket_node": # 该节点序号对应的是保存图片到websocket节点
                images_output = output_images.get(current_node, [])
                images_output.append(out[8:])
                output_images[current_node] = images_output

    return output_images

def show_image(images):
    for node_id in images:
        for image_data in images[node_id]:
            import io
            image = Image.open(io.BytesIO(image_data))
            image.show()


if __name__ == "__main__":
    prompt = get_imh2img_prompt(IMAGE_PATH, WORKFLOW_JSON_PATH)
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    imgs = get_images(ws, prompt)
    ws.close()
    show_image(imgs)


            
        

        

        