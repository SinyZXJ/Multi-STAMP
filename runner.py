import torch
import ray
from network import AttentionNet
from worker import Worker
from arguments import arg

@ray.remote(num_cpus=1, num_gpus=len(arg.cuda_devices) / arg.num_meta)
class Runner(object):
    def __init__(self, meta_id):
        self.meta_id = meta_id
        self.device = torch.device('cuda') if arg.use_gpu_runner else torch.device('cpu')
        self.local_net = AttentionNet(arg.embedding_dim)
        self.local_net.to(self.device)

    def get_weights(self):
        return self.local_net.state_dict()

    def set_weights(self, weights):
        self.local_net.load_state_dict(weights)

    def job(self, global_weights, episode_number, budget_size, graph_size, history_size, target_size):
        print(f'\033[92mmeta{self.meta_id:02}:\033[0m episode {episode_number} starts')
        self.set_weights(global_weights)
        # 是否保存图像
        save_img = (arg.save_img_gap != 0 and episode_number % arg.save_img_gap == 0 and episode_number != 0)

        worker = Worker(
            meta_id=self.meta_id,
            local_net=self.local_net,
            global_step=episode_number,
            budget_size=budget_size,
            graph_size=graph_size,
            history_size=history_size,
            target_size=target_size,
            device=self.device,
            greedy=False,
            save_image=save_img
        )
        job_results, metrics = worker.run_episode(episode_number)
        return job_results, metrics
