from fedasync import UpdaterThread
import copy
import torch


class Avg:
    def update_server_weights(self, updater_thread: UpdaterThread, c_id, client_weights, data_sum, time_stamp, epoch, update_param):
        updated_parameters = {}
        server_weights = copy.deepcopy(updater_thread.server_network.state_dict())

        for key, var in client_weights.items():
            updated_parameters[key] = var.clone()
            if torch.cuda.is_available():
                updated_parameters[key] = updated_parameters[key].cuda()
        for key, var in server_weights.items():
            updated_parameters[key] = (updated_parameters[key] + server_weights[key]) / 2
        return updated_parameters
