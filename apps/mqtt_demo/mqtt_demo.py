import appdaemon.plugins.mqtt.mqttapi as mqtt


class mqtt_demo(mqtt.Mqtt):

    def initialize(self):
        self.log("__function__: MQTT DEMO Listening")
        self.listen_event(self.mqtt_message,
                          'MQTT_MESSAGE')
        self.jarvis = self.get_app('jarvis_core')

    def mqtt_message(self, event_name, data, *args, **kwargs):
        self.log("__function__: %s" % data)
        self.jarvis.event_listener(event_name, data, *args, **kwargs)
