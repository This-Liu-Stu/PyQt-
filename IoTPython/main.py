import sys
import json
import ssl
import time
from datetime import datetime
import paho.mqtt.client as mqtt
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QToolTip
from PyQt5.QtGui import QCursor
from PyQt5 import QtCore, QtGui

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import font_manager
from matplotlib.figure import Figure

from mainwindow import Ui_MainWindow

# 阿里云提供的MQTT参数
params = {
    "clientId": "k0796zJ6ms6.PythonDev|securemode=2,signmethod=hmacsha256,timestamp=1725429662666|",
    "username": "PythonDev&k0796zJ6ms6",
    "mqttHostUrl": "iot-06z00god4hf1dy1.mqtt.iothub.aliyuncs.com",
    "passwd": "15d7624af708cdfb047112f891b4391e64c70e7f19c33831d0fcc565cbd0d608",
    "port": 1883
}

#发布Topic
topic_pub = "/sys/k0796zJ6ms6/PythonDev/thing/event/property/post"

# 初始化数据存储
timestamps = []
temperature = []
humidity = []
light = []

class MyMainForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init_mqtt()
        self.connect_to_mqtt()
        self.setup_buttons()  # Ensure this is called
        self.setup_plot()  # Setup plot widget
        self.plot_data()  # Start plotting data
    def init_mqtt(self):
        self.client = mqtt.Client(client_id=params["clientId"])
        self.client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_NONE,
                            tls_version=ssl.PROTOCOL_TLS)
        self.client.username_pw_set(params["username"], params["passwd"])
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.QLabel.setText(_translate("MainWindow", "湿度"))
        self.Humi.setText(_translate("MainWindow", "NULL"))
        self.QLabel_2.setText(_translate("MainWindow", "温度"))
        self.Temp.setText(_translate("MainWindow", "NULL"))
        self.QLabel_3.setText(_translate("MainWindow", "光照"))
        self.Light.setText(_translate("MainWindow", "NULL"))
        self.connect.setText(_translate("MainWindow", "服务器断开"))
        self.QLabel_4.setText(_translate("MainWindow", "风扇"))
        self.QLabel_5.setText(_translate("MainWindow", "水泵"))

        # Assume connectimage is a QLabel in the Ui_MainWindow
        self.connectimage = self.findChild(QLabel, 'connectimage')

    def setup_plot(self):
        # Create a new QWidget for the plot
        self.plot_widget = QWidget(self)
        self.plot_widget.setGeometry(10, self.height() - 370, 780,
                                     350)  # Adjust y to -300 for higher, width to 600 for wider

        # Create a Matplotlib Figure and FigureCanvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self.plot_widget)

        # Create a layout to hold the canvas
        self.plot_layout = QVBoxLayout()
        self.plot_layout.addWidget(self.canvas)
        self.plot_widget.setLayout(self.plot_layout)

        # Add the plot to the figure
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Sensor Data Over Time')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Value')

        # Initialize plot lines with improved styles
        self.line_temp, = self.ax.plot([], [], label='Temperature', color='red', linestyle='-', linewidth=2)
        self.line_humi, = self.ax.plot([], [], label='Humidity', color='blue', linestyle='--', linewidth=2)
        self.line_light, = self.ax.plot([], [], label='Light', color='green', linestyle='-.', linewidth=2)
        self.ax.legend()
        self.ax.grid(True)

        self.canvas.draw()

        # Connect the event handler
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def plot_data(self):
        if len(timestamps) > 0:
            self.line_temp.set_xdata(range(len(temperature)))
            self.line_temp.set_ydata(temperature)
            self.line_humi.set_xdata(range(len(humidity)))
            self.line_humi.set_ydata(humidity)
            self.line_light.set_xdata(range(len(light)))
            self.line_light.set_ydata(light)

            # Adjust x-axis limits to keep the plot scrolling
            self.ax.set_xlim(max(0, len(timestamps) - 50), len(timestamps))

            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
        QtCore.QTimer.singleShot(1000, self.plot_data)  # Update every second

    def on_mouse_move(self, event):
        if event.inaxes != self.ax:
            return

        xdata = [line.get_xdata() for line in [self.line_temp, self.line_humi, self.line_light]]
        ydata = [line.get_ydata() for line in [self.line_temp, self.line_humi, self.line_light]]

        xdata_flat = [item for sublist in xdata for item in sublist]
        ydata_flat = [item for sublist in ydata for item in sublist]

        if not xdata_flat or not ydata_flat:
            return

        distance = [abs(x - event.xdata) for x in xdata_flat]

        if not distance:
            return

        index = distance.index(min(distance))

        timestamp_index = index % len(timestamps)
        temp = temperature[timestamp_index] if len(temperature) > timestamp_index else 'N/A'
        humi = humidity[timestamp_index] if len(humidity) > timestamp_index else 'N/A'
        light_val = light[timestamp_index] if len(light) > timestamp_index else 'N/A'
        time_str = timestamps[timestamp_index].strftime('%Y-%m-%d %H:%M:%S')

        QToolTip.showText(QCursor.pos(),f"Temperature: {temp} °C\nHumidity: {humi} %\nLight: {light_val} lux\nTime: {time_str}")

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        if rc == 0:
            self.connect.setText("服务器连接")

            image = QtGui.QPixmap('image/connect/yes.png')
            resized_image = image.scaled(30, 30, QtCore.Qt.KeepAspectRatio)
            self.connectimage.setPixmap(resized_image)
        else:
            self.connect.setText("服务器断开")

            image = QtGui.QPixmap('image/connect/no.png')
            resized_image = image.scaled(30, 30, QtCore.Qt.KeepAspectRatio)
            self.connectimage.setPixmap(resized_image)
        client.subscribe("Topic")  # Ensure this topic is correct

    def on_message(self, client, userdata, msg):
        global timestamps, temperature, humidity, light
        print("Received message: " + str(msg.payload))
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            items = payload.get("items", {})

            temp = items.get("Temp", {}).get("value")
            humi = items.get("Humi", {}).get("value")
            light_val = items.get("Light", {}).get("value")

            current_time = datetime.now()
            timestamps.append(current_time)

            # Use previous values if new data is unavailable
            if temp is not None:
                temperature.append(temp)#temperature.append(int(temp))
            else:
                temperature.append(temperature[-1] if temperature else 0)

            if humi is not None:
                humidity.append(int(humi))
            else:
                humidity.append(humidity[-1] if humidity else 0)

            if light_val is not None:
                light.append(int(light_val))
            else:
                light.append(light[-1] if light else 0)

            # Maintain only the latest 100 entries
            if len(timestamps) > 100:
                timestamps = timestamps[1:]
                temperature = temperature[1:]
                humidity = humidity[1:]
                light = light[1:]

            self.Temp.setText(f"{temperature[-1]} °C")
            self.Humi.setText(f"{humidity[-1]} %")
            self.Light.setText(f"{light[-1]} lux")

        except json.JSONDecodeError:
            QMessageBox.critical(self, "消息解析错误", "无法解析接收到的消息数据。")
        except ValueError as e:
            QMessageBox.critical(self, "数据处理错误", f"处理接收到的数据时发生错误: {e}")

    def publish_message(self, topic, message):
        self.client.publish(topic, json.dumps(message), qos=1)

    def connect_to_mqtt(self):
        while True:
            try:
                self.client.connect(params["mqttHostUrl"], params["port"], 60)
                self.client.loop_start()
                break  # Exit loop once connected successfully
            except Exception as e:
                print(f"MQTT连接错误: {e}")
                time.sleep(10)  # Wait for 10 seconds before retrying

    def setup_buttons(self):
        self.wind_on_button = self.findChild(QPushButton, 'wind_on_button')
        self.wind_off_button = self.findChild(QPushButton, 'wind_off_button')
        self.water_on_button = self.findChild(QPushButton, 'water_on_button')
        self.water_off_button = self.findChild(QPushButton, 'water_off_button')

        self.wind_on_button.clicked.connect(self.publish_wind_on)
        self.wind_off_button.clicked.connect(self.publish_wind_off)
        self.water_on_button.clicked.connect(self.publish_water_on)
        self.water_off_button.clicked.connect(self.publish_water_off)

    def publish_wind_on(self):
        print("wind_on\n")
        message_content = {
            "params": {"Wind": 1},
            "version": "1.0"
        }
        self.publish_message(topic_pub, message_content)

    def publish_wind_off(self):
        print("wind_off\n")
        message_content = {
            "params": {"Wind": 0},
            "version": "1.0"
        }
        self.publish_message(topic_pub, message_content)

    def publish_water_on(self):
        print("water_on\n")
        message_content = {
            "params": {"Water": 1},
            "version": "1.0"
        }
        self.publish_message(topic_pub, message_content)

    def publish_water_off(self):
        print("water_off\n")
        message_content = {
            "params": {"Water": 0},
            "version": "1.0"
        }
        self.publish_message(topic_pub, message_content)

# 程序入口，程序从此处启动PyQt设计的窗体
if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = MyMainForm()  # 使用自定义的 MyMainForm 类
    MainWindow.show()  # 显示窗体
    sys.exit(app.exec_())  # 程序关闭时退出进程
