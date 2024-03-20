from clientmanager.BaseClientManager import BaseClientManager
from core.Runtime import CLIENT_STATUS
from utils import ModuleFindTool
from utils.GlobalVarGetter import GlobalVarGetter
from utils.ProcessManager import EventFactory


class NormalClientManager(BaseClientManager):
    def __init__(self, whole_config):
        super().__init__(whole_config)
        self.global_var = GlobalVarGetter.get()
        self.client_list = []  # client实例列表
        self.client_id_list = []  # 每个client对应的client id
        self.client_status = []  # 每个client的状态

        self.multi_gpu = whole_config["global"]["multi_gpu"]
        self.clients_num = whole_config["global"]["client_num"]
        self.client_staleness_list = whole_config["client_manager"]["stale_list"]
        self.index_list = whole_config["client_manager"]["index_list"]  # 每个client下的数据集index
        self.client_config = whole_config["client"]

        self.client_class = ModuleFindTool.find_class_by_path(whole_config["client"]["path"])
        self.stop_event_list = [EventFactory.create_Event() for _ in range(self.clients_num)]
        self.selected_event_list = [EventFactory.create_Event() for _ in range(self.clients_num)]
        self.global_var['selected_event_list'] = self.selected_event_list

    def start_all_clients(self):
        self.__init_clients()
        # 启动clients
        self.global_var['client_list'] = self.client_list
        self.global_var['client_id_list'] = self.client_id_list
        print("Start clients:")
        for i in self.client_id_list:
            self.client_list[i].start()
            self.client_status[i] = CLIENT_STATUS['active']

    def __init_clients(self):
        client_dev = self.get_client_dev_list(self.clients_num, self.multi_gpu)
        for i in range(self.clients_num):
            client_delay = self.client_staleness_list[i]
            self.client_list.append(
                self.client_class(i, self.stop_event_list[i], self.selected_event_list[i], client_delay,
                                  self.index_list[i], self.client_config, client_dev[i]))  # 实例化
            self.client_status.append(CLIENT_STATUS['created'])
            self.client_id_list.append(i)

    def get_client_list(self):
        client_list = self.client_list
        return client_list

    def get_client_id_list(self):
        return self.client_id_list

    def stop_all_clients(self):
        # 终止所有client线程
        for i in range(self.clients_num):
            self.stop_client_by_id(i)
            self.client_status[i] = CLIENT_STATUS['stopped']

    def stop_client_by_id(self, client_id):
        self.stop_event_list[client_id].set()
        self.selected_event_list[client_id].set()

    def create_and_start_new_client(self, client_delay, dev='cpu'):
        client_id = len(self.client_list)
        self.client_list.append(
            self.client_class(client_id, self.stop_event_list[client_id], self.selected_event_list[client_id], client_delay,
                              self.index_list[client_id], self.client_config, dev))  # 实例化
        self.client_id_list.append(client_id)
        self.client_list[client_id].start()
        self.client_status.append(CLIENT_STATUS['active'])
        self.clients_num += 1

    def client_join(self):
        for i in self.client_list:
            i.join()
