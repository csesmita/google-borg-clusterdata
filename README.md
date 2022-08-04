# google-borg-clusterdata
Describes the process of acquiring a textual representation of job workload using Google Borg's traces from 2019 (https://github.com/google/cluster-data).

The following trace captures a set of jobs from the original workload for which tasks and their running time information was found to be complete. It has a total of 990042 jobs. They are taken from the production class of the These jobs are representative of the Google workload, and can be used for analyzing various scheduling designs.

Note that this workload does not contain any usage information or resource requests.

## Location of Traces
TODO

## Format of Workload Traces
The .txt file describes one job per line. Each job description consists of -
1. Job Arrival Time in seconds from epoch.
2. Number of Tasks of the job.
3. Estimated running time of tasks of the job.
4. A list of actual running times of tasks of the job.

## How the Traces were Obtained
The traces are derived from Borg Cluster Workload Traces 2019 (version 3). As mentioned, this workload trace does not capture any machine information or resource information. It also does not concern itself with allocation sets. It only derives all production jobs that finished successfully, and have record of one or more tasks that finished successfully.

### CollectionEvents Table
1. Time - Converted to seconds from microseconds from epoch.
2. Type - Submit or Finish. 
3. Collection Type - 0 (Job)
4. Priority - 200 (Production Job)
5. Scheduler = 0 (default)
6. Collection Id - To identify tasks that belong to it.

### InstanceEvents Table
1. Time
2. Type - 3 (Schedule) or 6 (Finish)
3. Collection Type = 0 (Job / Task)
4. Priority - 200
5. Instance Index

### Algorithm - Calculating job characteristics
1. Fetch job start and end times using the Submit and Finish events respectively.
2. Fetch a task from the instance events table. If it does not match any collection_id in #1, then do nothing. Else continue.
3. If the task event time does not lie within the start and end times of the matched collection_id in #1, then do nothing. Else continue.
4. If the task event type is not schedule or finish, then do nothing. Else continue.
5. If the event does not have a machine assigned (might be a synthetic data point), then do nothing. Else continue.
6. Compute task running time as the time between schedule and finish events of the task. (There can be multiple machines that have schedule and finish events for a task. We compute the running time as the average of running times on each of these machines.)
7. Compute estimated task running time as the average of all tasks identified for this job.

The attached script (workload_generator.py) is the actual implementation of the algorithm.
