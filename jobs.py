import json
import glob
import numpy as np

workload_file = open('workload.json', 'w')
job_start={}
job_finish={}
job_task = {}
workload_info={}
with open('/local/scratch/google-workload/collection-event/jobs_submit.json', 'r') as f:
    for row in f:
        data = json.loads(row)
        job_id = data['collection_id']
        #job_name = data['collection_name']
        job_time = int(data['time'])
        job_start[job_id] = job_time / 1000000.0
        #output_file.write('%s  %s' % (job_name, job_time))
with open('/local/scratch/google-workload/collection-event/jobs_finish.json', 'r') as f:
    for row in f:
        data = json.loads(row)
        job_id = data['collection_id']
        #job_name = data['collection_name']
        job_time = int(data['time'])
        job_finish[job_id] = job_time / 1000000.0
        #output_file.write('%s  %s' % (job_name, job_time))
job_ids = set(set(job_start.keys())  & set(job_finish.keys()))
EVENT_SCHEDULE = 3 
EVENT_FINISH = 6 
tasks_dict = {}
files = [file_name for file_name in glob.glob('/local/scratch/google-workload/instance-event/tasks_*.json')]
for file_name in files:
    print("Processing file", file_name)
    with open(file_name, 'r') as f:
        for row in f:
            try:
                row = (row.split('.json:'))[1]
            except:
                pass
            data = json.loads(row)
            job_id = data['collection_id']
            if job_id not in job_ids:
                continue
            event_time = int(data['time']) / 1000000.0
            if event_time < job_start[job_id] or event_time > job_finish[job_id]:
                continue
            event_type = int(data['type'])
            if event_type != EVENT_SCHEDULE and event_type != EVENT_FINISH:
                continue
            try:
                machine_id = data['machine_id']
            except:
                #print("Exception - Got machine id 0 in this task event - ", data)
                continue
            if machine_id == '0':
                raise AssertionError("Got machine id 0 in this task event - ", data)
            task_id = data['instance_index']
            if job_id not in job_task.keys():
                job_task[job_id] = set()
            job_task[job_id].add(task_id)
            #Collect all events of this task
            key = job_id + task_id
            if key not in tasks_dict.keys():
                tasks_dict[key] = []
            tasks_dict[key].append((job_id, event_time, event_type, machine_id))

    task_estimated_running_times = {}
    for task_id, task_events in tasks_dict.items():
        machine_events = {}
        for job_id, time, event_type, machine_id in task_events:
            if machine_id not in machine_events.keys():
                machine_events[machine_id] = {}
            if event_type == EVENT_SCHEDULE:
                if EVENT_SCHEDULE not in machine_events[machine_id]:
                    machine_events[machine_id][EVENT_SCHEDULE] = time
                else:
                    if time > machine_events[machine_id][EVENT_SCHEDULE]:
                        machine_events[machine_id][EVENT_SCHEDULE] = time
            if event_type == EVENT_FINISH:
                if EVENT_FINISH not in machine_events[machine_id]:
                    machine_events[machine_id][EVENT_FINISH] = time
                else:
                    if time > machine_events[machine_id][EVENT_FINISH]:
                        machine_events[machine_id][EVENT_FINISH] = time
        est_time = 0
        count = 0
        for machine_id, machine_events_list in machine_events.items():
            #There are many machines where finish is not a part of the event. Discard those.
            if EVENT_SCHEDULE in machine_events_list.keys() and EVENT_FINISH in machine_events_list.keys():
                task_start = machine_events_list[EVENT_SCHEDULE]
                task_end = machine_events_list[EVENT_FINISH]
                est_time += task_end - task_start
                count += 1
        if count > 0:
            if job_id not in task_estimated_running_times.keys():
                task_estimated_running_times[job_id] = []
            task_estimated_running_times[job_id].append(est_time / count)
#We are ready to generate the file. Sort the start times and 
job_start_sorted = {k:v for k,v in sorted(job_start.items(), key=lambda item: item[1])}
for job_id, est_array in task_estimated_running_times.items():
    num_tasks = len(est_array)
    job_est_time = sum(est_array) / num_tasks
    workload_file.write('%f %d %f %s\n' %(job_start[job_id], num_tasks, job_est_time, ' '.join(map(str, est_array))))
workload_file.close()
