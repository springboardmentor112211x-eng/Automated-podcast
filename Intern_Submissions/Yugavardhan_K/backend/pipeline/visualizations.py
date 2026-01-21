import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_topic_timeline(topics, out):
    if not topics:
        return

    plt.figure(figsize=(12, 2))
    for t in topics:
        plt.barh(1, t["end_time"] - t["start_time"], left=t["start_time"])
    plt.yticks([])
    plt.savefig(out)
    plt.close()