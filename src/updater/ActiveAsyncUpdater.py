import copy
import time

from updater.AsyncUpdater import AsyncUpdater
from core.MessageQueue import MessageQueueFactory


class ActiveAsyncUpdater(AsyncUpdater):
    def __init__(self, server_thread_lock, stop_event, config, mutex_sem, empty_sem, full_sem):
        super().__init__(server_thread_lock, stop_event, config, mutex_sem, empty_sem, full_sem)
        self.message_queue = MessageQueueFactory.create_message_queue()

    def run(self):
        for epoch in range(self.T):
            self.full_sem.acquire()
            self.mutex_sem.acquire()
            while True:
                # 接收一个client发回的模型参数和时间戳
                if not self.queue_manager.empty():
                    # 等待上传
                    self.nums = self.num_generator.get_num()
                    self.queue_manager.receive(self.nums)
                    update_list = []
                    for i in range(self.nums):
                        update_list.append(self.queue_manager.get())
                        c_id = update_list[i]["client_id"]
                        time_stamp = update_list[i]["time_stamp"]
                        self.sum_delay += (self.current_time.get_time() - time_stamp)
                        print("Updater received data from client", c_id, "| staleness =", time_stamp, "-",
                              self.current_time.get_time(), "| queue size = ", self.queue_manager.size())
                    self.event.set()
                else:
                    update_list = []

                if self.event.is_set():
                    # 使用接收的client发回的模型参数和时间戳对全局模型进行更新
                    self.server_thread_lock.acquire()
                    self.update_server_weights(epoch, update_list)
                    self.run_server_test(epoch)
                    self.message_queue.set_latest_model(copy.deepcopy(self.server_network.state_dict()), epoch)
                    self.server_thread_lock.release()
                    self.event.clear()
                    time.sleep(0.01)
                    break
                else:
                    time.sleep(0.01)

            self.current_time.time_add()
            self.mutex_sem.release()
            self.empty_sem.release()
            time.sleep(0.01)

        print("Average delay =", (self.sum_delay / self.T))
