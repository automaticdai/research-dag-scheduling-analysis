from rta_alphabeta_new import experiment
from analysis import generate_results

if __name__ == "__main__":
    print("========================================================")
    print("RTSS'2020 Artifacts Evaluation")
    print("This is the AE for the following work:")
    print("\"DAG Scheduling and Analysis on Multiprocessor Systems\"")
    print("========================================================")

    print("Running experiment 1/4:")
    experiment(1)

    print("========================================================")
    print("Running experiment 2/4:")
    experiment(2)

    print("========================================================")
    print("Running experiment 3/4:")
    experiment(3)

    print("========================================================")
    print("Running experiment 4/4:")
    experiment(4)

    print("========================================================")
    print("Raw data collection is finished!")
    print("========================================================")

    print("Starting to produce diagrams:")
    generate_results()

    print("========================================================")
    print("All Completed!")
    print("========================================================")
    
