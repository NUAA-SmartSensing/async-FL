import threading
from abc import abstractmethod

from core.MessageQueue import MessageQueueFactory
from schedule.ScheduleCaller import ScheduleCaller
from utils import ModuleFindTool
from utils.GlobalVarGetter import GlobalVarGetter
from utils.Tools import to_cpu, random_seed_set


class BaseScheduler(threading.Thread):
    def __init__(self, server_thread_lock, config):
        threading.Thread.__init__(self)
        self.server_thread_lock = server_thread_lock
        self.config = config

        self.global_var = GlobalVarGetter.get()
        random_seed_set(self.global_var['global_config']['seed'])

        self.selected_event_list = self.global_var['selected_event_list']
        self.current_t = self.global_var['current_t']
        self.schedule_t = self.global_var['schedule_t']
        self.server_network = self.global_var['server_network']
        self.T = self.global_var['T']
        self.queue_manager = self.global_var['queue_manager']

        self.server_weights = self.server_network.state_dict()

        schedule_class = ModuleFindTool.find_class_by_path(config["schedule"]["path"])
        self.schedule_method = schedule_class(config["schedule"]["params"])
        self.schedule_caller = ScheduleCaller(self)

        self.message_queue = MessageQueueFactory.create_message_queue()

    @abstractmethod
    def run(self):
        pass

    def client_select(self, *args, **kwargs):
        client_list = self.global_var['client_id_list']
        training_status = self.message_queue.get_training_status()
        client_list = [client_id for client_id in client_list if client_id not in training_status or not training_status[client_id]]
        selected_clients = self.schedule_caller.schedule(client_list)
        return selected_clients

    def send_weights(self, client_id, current_time, schedule_time):
        self.message_queue.put_into_downlink(client_id, 'weights_buffer', to_cpu(self.server_weights))
        self.message_queue.put_into_downlink(client_id, 'time_stamp_buffer', current_time)
        self.message_queue.put_into_downlink(client_id, 'schedule_time_stamp_buffer', schedule_time)
        self.message_queue.put_into_downlink(client_id, 'received_weights', True)
        self.message_queue.put_into_downlink(client_id, 'received_time_stamp', True)

