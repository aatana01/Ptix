import ast
import copy
import csv
import os
import re
import statistics
import sys
#import matplotlib.pyplot as plt
#import matplotlib.backends.backend_pdf

def derive_datatype(datastr):
    try:
        return type(ast.literal_eval(datastr))
    except:
        return type("")

def system_conf_fullname(system_conf):
    l = [
        'turbo={}'.format(system_conf['turbo']),
        'kernelconfig={}'.format(system_conf['kernelconfig']),
        'hyperthreading={}'.format(system_conf['ht'])
    ]
    if 'freq' in system_conf:
        l.append('freq={}'.format(system_conf['freq']))
    return '-'.join(l) + '-'

def system_conf_shortname(system_conf):
    short_kernelconfig = {
        'baseline': 'baseline',
        'disable_cstates': 'no_cstates',
        'disable_c6': 'no_c6',
        'disable_c1e_c6': 'no_c1e_c6',
        'quick_c1': 'q_c1',
        'quick_c1_c1e': 'q_c1_c1e',
        'quick_c1_disable_c6': 'q_c1-no_c6',
    }
    l = [
        'T' if system_conf['turbo'] else 'NT',
        short_kernelconfig[system_conf['kernelconfig']],
    ]
    if 'freq' in system_conf:
        l.append('F{}'.format(system_conf['freq']))
    return '-'.join(l) + '-'

def shortname(qps=None):
    return 'qps={}'.format(qps)

def parse_mcperf_stats(mcperf_results_path):
    stats = None
    with open(mcperf_results_path, 'r') as f:
        stats = {}
        for l in f:
            if l.startswith('#type'):
                stat_names = l.split()[1:]
                read_stats = next(f).split()[1:]
                update_stats = next(f).split()[1:]
                read_stats_dict = {}
                update_stats_dict = {}
                for i, stat_name in enumerate(stat_names):
                    read_stats_dict[stat_name] = float(read_stats[i])
                    update_stats_dict[stat_name] = float(update_stats[i])
                stats['read'] = read_stats_dict
                stats['update'] = update_stats_dict
            if l.startswith('Total QPS'):
                stats['total_qps'] = float(l.split()[3])
    return stats

def read_timeseries(filepath):
    header = None
    timeseries = None
    with open(filepath, 'r') as f:
        header = f.readline().strip()
        timeseries = []
        data = f.readline().strip().split(',')
        datatype = derive_datatype(data[1])
        f.seek(0)
        for l in f.readlines()[1:]:
            data = l.strip().split(',')
            timestamp = int(data[0])
            value = datatype(data[1])
            timeseries.append((timestamp, value))
    return (header, timeseries)            

def add_metric_to_dict(stats_dict, metric_name, metric_value):
    head = metric_name.split('.')[0]
    tail = metric_name.split('.')[1:]
    if tail:
        stats_dict = stats_dict.setdefault(head, {})
        add_metric_to_dict(stats_dict, '.'.join(tail), metric_value)
    else:
        stats_dict[head] = metric_value

def parse_cstate_stats(stats_dir):
    stats = {}
    prog = re.compile('(.*)\.(.*)\.(.*)')
    for f in os.listdir(stats_dir):
        m = prog.match(f)
        if m:
            stats_file = os.path.join(stats_dir, f)
            cpu_id = m.group(1)
            state_name = m.group(2)
            metric_name = m.group(3)
            (metric_name, timeseries) = read_timeseries(stats_file)
            add_metric_to_dict(stats, metric_name, timeseries)
    return stats

def parse_perf_stats(stats_dir):
    stats = {}
    prog = re.compile('(.*)\.(.*)\.(.*)')
    for f in os.listdir(stats_dir):
        m = prog.match(f)
        if not m:
            stats_file = os.path.join(stats_dir, f)
            (metric_name, timeseries) = read_timeseries(stats_file)
            add_metric_to_dict(stats, metric_name, timeseries)
    return stats
    
def parse_pkgcstate_stats(stats_dir):
    stats={}
    prog = re.compile('(.*)\.(.*)\.(.*)')
    for f in os.listdir(stats_dir):
        m = prog.match(f)
        if m:
            stats_file = os.path.join(stats_dir, f)
            cpu_id = m.group(1)
            state_name = m.group(2)
            metric_name = m.group(3)
            (metric_name, timeseries) = read_timeseries(stats_file)
            add_metric_to_dict(stats, metric_name, timeseries)

def parse_util_stats(util_stats_dirs):
    
    stats={}
    f="cpu_util"
    stats_file = os.path.join(util_stats_dirs, f)
    (metric_name, timeseries) = read_timeseries(stats_file)
    add_metric_to_dict(stats, metric_name, timeseries)
    return stats
    
def parse_rapl_stats(rapl_stats_file):
    stats = {}
    counter=0
    stats['package-0'] = []
    stats['package-1'] = []
    stats['ram-0'] = []
    stats['ram-1'] = []
    package_0=0
    package_1=0
    ram_0=0
    ram_1=0
    
    with open(rapl_stats_file, 'r') as f:
        for l in f: 
            
            if counter%4==0:
                package_0=int(l)-package_0                
            elif counter%4==1:
                package_1=int(l)-package_1
            elif counter%4==2:
                ram_0=int(l)-ram_0
            elif counter%4==3:
                ram_1=int(l)-ram_1
            counter=counter+1
            
        stats['package-0'].append(float(package_0/120/1000000))
        stats['package-1'].append(float(package_1/120/1000000))
        stats['ram-0'].append(float(ram_0/120/1000000))
        stats['ram-1'].append(float(ram_1/120/1000000))
        print(stats)
        
    return stats

def parse_single_instance_stats(stats_dir):
    stats = {}
    
    
    server_cstate_stats = parse_cstate_stats(stats_dir)
    server_perf_stats = parse_perf_stats(stats_dir)
    stats['server'] = {**server_cstate_stats, **server_perf_stats}
    
    return stats

def parse_multiple_instances_stats(stats_dir, pattern='.*'):
    stats = {}
    for f in os.listdir(stats_dir):
        instance_dir = os.path.join(stats_dir, f)
        instance_name = f[:f.rfind('-')]
        stats.setdefault(instance_name, []).append(parse_single_instance_stats(instance_dir))
    return stats

def cpu_state_time_perc(data, cpu_id):
    cpu_str = "CPU{}".format(cpu_id)
    state_names = ['POLL', 'C1', 'C1E', 'C6']
    state_time_perc = []
    total_state_time = 0
    time_us = 0
    # determine time window of measurements
    for state_name in state_names:
        if state_name in data[cpu_str]:
            (ts_start, val_start) = data[cpu_str][state_name]['time'][0]
            (ts_end, val_end) = data[cpu_str][state_name]['time'][-1]
            time_us = max(time_us, (ts_end - ts_start) * 1000000.0)
            total_state_time += val_end - val_start    
    time_us = max(time_us, total_state_time)
    # FIXME: time duration is currently hardcoded at 120s (120000000us)
    extra_c6_time_us = time_us - 60000000
    # calculate percentage
    for state_name in state_names:
        if state_name == 'C6':
            extra = extra_c6_time_us
        else:
            extra = 0
        if state_name in data[cpu_str]:
            (ts_start, val_start) = data[cpu_str][state_name]['time'][0]
            (ts_end, val_end) = data[cpu_str][state_name]['time'][-1]
            state_time_perc.append((val_end-val_start-extra)/time_us)
    # calculate C0 as the remaining time 
    state_time_perc[0] = 1 - sum(state_time_perc[1:4])
    state_names[0] = 'C0' 
    return state_time_perc

def avg_state_time_perc(stats, cpu_id_list):
    for stat in stats:
        total_state_time_perc = [0]*4
        cpu_count = 0
        for cpud_id in cpu_id_list:
            cpu_count += 1
            total_state_time_perc = [a + b for a, b in zip(total_state_time_perc, cpu_state_time_perc(stats, cpud_id))]
        avg_state_time_perc = [a/b for a, b in zip(total_state_time_perc, [cpu_count]*len(total_state_time_perc))]
    return avg_state_time_perc

def get_residency_per_target_qps(stats, stats_root_dir):
    # determine used C-states
    state_names = ['C0']
    check_state_names = ['C1', 'C1E', 'C6']
    for state_name in check_state_names:
        instance_name = stats_root_dir
        
        if state_name in stats[instance_name][0]['server']['CPU0']:
            state_names.append(state_name)
   
    raw = [[]] * (1+len(state_names))
    raw[0] = (['State'])
    for state_id in range(0, len(state_names)):
        raw[1+state_id] = [state_names[state_id]]
    
    instance_name = stats_root_dir
    time_perc_list = []
    for stat in stats[instance_name]:
            
        time_perc_list.append(avg_state_time_perc(stat['server'], range(0, 40)))
    avg_time_perc = [0]*len(state_names)
    for time_perc in time_perc_list:
        avg_time_perc = [a+b for a, b in zip(avg_time_perc, time_perc)]
    avg_time_perc = [a/len(time_perc_list) for a in avg_time_perc]
    for state_id in range(0, len(state_names)):
        row = raw[1 + state_id]
        row.append(avg_time_perc[state_id])
    return raw

def cpu_state_usage(data, cpu_id):
    cpu_str = "CPU{}".format(cpu_id)
    state_names = ['POLL', 'C1', 'C1E', 'C6']
    state_time_perc = []
    total_state_time = 0
    time_us = 0
    state_usage_vec = []
    for state_name in state_names:
        if state_name in data[cpu_str]:
            (ts_start, val_start) = data[cpu_str][state_name]['usage'][0]
            (ts_end, val_end) = data[cpu_str][state_name]['usage'][-1]
            state_usage = val_end - val_start
            state_usage_vec.append(state_usage)
    return state_usage_vec

def avg_state_usage(stats, cpu_id_list):
    total_state_usage = [0]*4
    cpu_count = 0
    for cpud_id in cpu_id_list:
        cpu_count += 1
        total_state_usage = [a + b for a, b in zip(total_state_usage, cpu_state_usage(stats, cpud_id))]
    avg_state_usage = [a/b for a, b in zip(total_state_usage, [cpu_count]*len(total_state_usage))]
    return avg_state_usage

def get_usage_per_target_qps(stats, stats_root_dir ):
    # determine used C-states
    state_names = ['POLL']
    check_state_names = ['C1', 'C1E', 'C6']
    for state_name in check_state_names:
        instance_name = stats_root_dir
        if state_name in stats[instance_name][0]['server']['CPU0']:
            state_names.append(state_name)
            
    raw = [[]] * (1+len(state_names))
    raw[0] = (['State'])
    for state_id in range(0, len(state_names)):
        raw[1+state_id] = [state_names[state_id]]
    
    instance_name = stats_root_dir
    usage_list = []
    for stat in stats[instance_name]:
        usage_list.append(avg_state_usage(stat['server'], range(0, 40)))
    avg_usage = [0]*len(state_names)
    for usage in usage_list:
        avg_usage = [a+b for a, b in zip(avg_usage, usage)]
    avg_usage = [a/len(usage_list) for a in avg_usage]
    for state_id in range(0, len(state_names)):
        row = raw[1 + state_id]
        row.append(avg_usage[state_id])
    return raw

def plot_residency_per_target_qps(stats, system_conf, qps_list):
    raw = get_residency_per_target_qps(stats, system_conf, qps_list)
    width = 0.35        
    fig, ax = plt.subplots()
    header_row = raw[0]
    bottom = [0] * len(header_row[1:])
    labels = [str(int(int(c)/1000))+'K' for c in header_row[1:]]
    for row in raw[1:]:
        state_name = row[0]
        vals = [float(c) for c in row[1:]]
        ax.bar(labels, vals, width, label=state_name, bottom=bottom)
        for i, val in enumerate(vals):
            bottom[i] += val    
    ax.set_ylabel('C-State Residency (fraction)')
    ax.set_xlabel('Request Rate (QPS)')
    ax.legend()
    plt.title(system_conf_fullname(system_conf))
    return fig

def get_latency_per_target_qps(stats, system_confs, qps_list):
    if not isinstance(system_confs, list):
        system_confs = [system_confs]
    raw = []
    header_row = []
    header_row.append('QPS')
    for system_conf in system_confs:
        header_row.append(system_conf_shortname(system_conf) + 'read_avg_avg') 
        header_row.append(system_conf_shortname(system_conf) + 'read_avg_std') 
        header_row.append(system_conf_shortname(system_conf) + 'read_p99_avg') 
        header_row.append(system_conf_shortname(system_conf) + 'read_p99_std') 
    raw.append(header_row)
    for i, qps in enumerate(qps_list):
        row = [str(qps)]
        for system_conf in system_confs:
                        
            read_avg = []
            read_p99 = []
            instance_name = system_conf_fullname(system_conf) + shortname(qps)
            for stat in stats[instance_name]:
                mcperf_stats = stat['mcperf']
                read_avg.append(mcperf_stats['read']['avg'])
                read_p99.append(mcperf_stats['read']['p99'])
            if len(read_avg) >= 5:
                read_avg.remove(min(read_avg))
                read_avg.remove(max(read_avg))
                read_p99.remove(min(read_p99))
                read_p99.remove(max(read_p99))
            row.append(str(statistics.mean(read_avg)))
            row.append(str(statistics.stdev(read_avg)) if len(read_avg) > 1 else 'N/A')
            row.append(str(statistics.mean(read_p99)))
            row.append(str(statistics.stdev(read_p99)) if len(read_p99) > 1 else 'N/A')
        raw.append(row)
    return raw

def column_matches(filter, column_name):
    for f in filter:
        if f in column_name:
            return True
    return False

def plot_X_per_target_qps(raw, qps_list, xlabel, ylabel, filter=None):
    axis_scale = 0.001
    fig, ax = plt.subplots()
    axis_qps_list = [q *axis_scale for q in qps_list]
    header_row = raw[0]
    data_rows = raw[1:]
    for i, y_column_name in enumerate(header_row[1::2]):
        if filter and not column_matches(filter, y_column_name):
            continue
        y_vals = []
        y_vals_err = []
        y_column_id = 1 + i * 2
        for row_id, row in enumerate(data_rows):
            y_vals.append(float(data_rows[row_id][y_column_id]))
            y_val_err = data_rows[row_id][y_column_id+1] 
            y_vals_err.append(float(y_val_err) if y_val_err != 'N/A' else 0)
        plt.errorbar(axis_qps_list, y_vals, yerr = y_vals_err, label=y_column_name)

    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.legend(loc='lower right')

    return fig

def plot_latency_per_target_qps(stats, system_confs, qps_list, filter=None):
    raw = get_latency_per_target_qps(stats, system_confs, qps_list)
    return plot_X_per_target_qps(raw, qps_list, 'Request Rate (KQPS)', 'Latency (us)', filter)

def get_total_qps_per_target_qps(stats, system_confs, qps_list):
    if not isinstance(system_confs, list):
        system_confs = [system_confs]
    raw = []
    header_row = []
    header_row.append('QPS')
    for system_conf in system_confs:
        header_row.append(system_conf_shortname(system_conf) + 'Total-QPS-avg') 
        header_row.append(system_conf_shortname(system_conf) + 'Total-QPS-std') 
    raw.append(header_row)
    for i, qps in enumerate(qps_list):
        row = [str(qps)]
        for system_conf in system_confs:
            total_qps = []
            instance_name = system_conf_fullname(system_conf) + shortname(qps)
            for stat in stats[instance_name]:
                mcperf_stats = stat['mcperf']
                total_qps.append(mcperf_stats['total_qps'])
            row.append(str(statistics.mean(total_qps)))
            row.append(str(statistics.stdev(total_qps)) if len(total_qps) > 1 else 'N/A')
        raw.append(row)
    return raw

def plot_total_qps_per_target_qps(stats, system_confs, qps_list, filter=None):
    raw = get_total_qps_per_target_qps(stats, system_confs, qps_list)
    return plot_X_per_target_qps(raw, qps_list, 'Request Rate (KQPS)', 'Total Rate (KQPS)', filter)

def avg_power(timeseries):
    total_val = 0
    for (ts, val) in timeseries:
        total_val += val
    time = timeseries[-1][0] - timeseries[0][0]
    return total_val / time

def avg_util(timeseries):
    total_val = 0
    for (ts, val) in timeseries:
        total_val += val
    time = timeseries[-1][0] - timeseries[0][0]
    return total_val / time

def get_power_per_target_qps(stats, stats_root_dir):
    
    raw = []
    header_row = []
    
    
    header_row.append('power-pkg-avg') 
    header_row.append('power-pkg-std') 
    header_row.append('power-ram-avg') 
    header_row.append('power-ram-std') 
    raw.append(header_row)
    power_pkg = []
    power_ram = []
    instance_name = stats_root_dir
    for stat in stats[instance_name]:
        system_stats = stat['server']
        power_pkg.append(avg_power(system_stats['power/energy-pkg/']))
        power_ram.append(avg_power(system_stats['power/energy-ram/']))
    row=[]
    row.append(str(statistics.mean(power_pkg)))
    row.append(str(statistics.stdev(power_pkg)) if len(power_pkg) > 1 else 'N/A' )
    row.append(str(statistics.mean(power_ram)))
    row.append(str(statistics.stdev(power_ram)) if len(power_ram) > 1 else 'N/A')
    raw.append(row)
    
    return raw

def get_util_per_target_qps(stats, system_confs, qps_list):
    if not isinstance(system_confs, list):
        system_confs = [system_confs]
    raw = []
    header_row = []
    header_row.append('QPS')
    for system_conf in system_confs:
        header_row.append(system_conf_shortname(system_conf) + 'cpu-util-avg') 
        header_row.append(system_conf_shortname(system_conf) + 'cpu-util-std') 
    raw.append(header_row)
    for i, qps in enumerate(qps_list):
        row = [str(qps)]
        for system_conf in system_confs:
            cpu_util = []
            instance_name = system_conf_fullname(system_conf) + shortname(qps)
            for stat in stats[instance_name]:
                system_stats = stat['server']
                cpu_util.append(avg_util(system_stats['cpu_util']))
            row.append(str(statistics.mean(cpu_util)*2))
            row.append(str(statistics.stdev(cpu_util)) if len(cpu_util) > 1 else 'N/A' )
        raw.append(row)
    return raw

def get_rapl_power_per_target_qps(stats, system_confs, qps_list):
    if not isinstance(system_confs, list):
        system_confs = [system_confs]
    raw = []
    header_row = []
    header_row.append('QPS')
    for system_conf in system_confs:
        header_row.append(system_conf_shortname(system_conf) + 'power-pkg-0-avg') 
        header_row.append(system_conf_shortname(system_conf) + 'power-pkg-0-std') 
        header_row.append(system_conf_shortname(system_conf) + 'power-pkg-1-avg') 
        header_row.append(system_conf_shortname(system_conf) + 'power-pkg-1-std') 
        header_row.append(system_conf_shortname(system_conf) + 'power-ram-0-avg') 
        header_row.append(system_conf_shortname(system_conf) + 'power-ram-0-std')
        header_row.append(system_conf_shortname(system_conf) + 'power-ram-1-avg') 
        header_row.append(system_conf_shortname(system_conf) + 'power-ram-1-std')
    raw.append(header_row)
    for i, qps in enumerate(qps_list):
        row = [str(qps)]
        for system_conf in system_confs:
            power_pkg_0 = []
            power_ram_0 = []
            power_pkg_1 = []
            power_ram_1 = []
            instance_name = system_conf_fullname(system_conf) + shortname(qps)
            for stat in stats[instance_name]:
                system_stats = stat['server']
                power_pkg_0.append((system_stats['package-0'][0]))
                power_pkg_1.append((system_stats['package-1'][0]))
                power_ram_0.append((system_stats['ram-0'][0]))
                power_ram_1.append((system_stats['ram-1'][0]))
            print(power_pkg_0)  
            row.append(str(statistics.mean(power_pkg_0)))
            row.append(str(statistics.stdev(power_pkg_0)) if len(power_pkg_0) > 1 else 'N/A' )
            row.append(str(statistics.mean(power_pkg_1)))
            row.append(str(statistics.stdev(power_pkg_1)) if len(power_pkg_1) > 1 else 'N/A' )
            row.append(str(statistics.mean(power_ram_0)))
            row.append(str(statistics.stdev(power_ram_0)) if len(power_ram_0) > 1 else 'N/A')
            row.append(str(statistics.mean(power_ram_1)))
            row.append(str(statistics.stdev(power_ram_1)) if len(power_ram_1) > 1 else 'N/A')
        raw.append(row)
    return raw

def plot_power_per_target_qps(stats, system_confs, qps_list, filter=None):
    raw = get_power_per_target_qps(stats,  qps_list)
    return plot_X_per_target_qps(raw, qps_list, 'Request Rate (KQPS)', 'Power (W)', filter)

def write_csv(filename, rows):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)    

def write_csv_all(stats, stats_root_dir):
   
        
    raw = get_residency_per_target_qps(stats, stats_root_dir)
    write_csv(stats_root_dir + 'residency_per_target_qps' + '.csv', raw)
  
    raw = get_power_per_target_qps(stats, stats_root_dir)
    write_csv(stats_root_dir + 'power_per_target_qps' + '.csv', raw)
    
    raw = get_usage_per_target_qps(stats, stats_root_dir)
    write_csv(stats_root_dir + 'usage_per_target_qps' + '.csv', raw)
             
        
def filter_system_confs(system_confs, turbo):
    turbo_system_confs = []
    for s in system_confs:
        if s['turbo'] == turbo:
            turbo_system_confs.append(s)
    return turbo_system_confs

def write_latency_to_single_csv(stats, system_confs, qps_list):
    turbo_system_confs = filter_system_confs(system_confs, turbo=True)
    turbo_raw = get_latency_per_target_qps(stats, turbo_system_confs, qps_list)
    noturbo_system_confs = filter_system_confs(system_confs, turbo=False)
    noturbo_raw = get_latency_per_target_qps(stats, noturbo_system_confs, qps_list)
    write_csv('all_latency_per_target_qps' + '.csv', turbo_raw + noturbo_raw)

def write_power_to_single_csv(stats, system_confs, qps_list):
    turbo_system_confs = filter_system_confs(system_confs, turbo=True)
    turbo_raw = get_power_per_target_qps(stats, turbo_system_confs, qps_list)
    noturbo_system_confs = filter_system_confs(system_confs, turbo=False)
    noturbo_raw = get_power_per_target_qps(stats, noturbo_system_confs, qps_list)
    write_csv('all_power_per_target_qps' + '.csv', turbo_raw + [] + noturbo_raw)

def write_total_qps_to_single_csv(stats, system_confs, qps_list):
    turbo_system_confs = filter_system_confs(system_confs, turbo=True)
    turbo_raw = get_total_qps_per_target_qps(stats, turbo_system_confs, qps_list)
    noturbo_system_confs = filter_system_confs(system_confs, turbo=False)
    noturbo_raw = get_total_qps_per_target_qps(stats, noturbo_system_confs, qps_list)
    write_csv('all_total_qps_per_target_qps' + '.csv', turbo_raw + noturbo_raw)

def plot(stats, system_confs, qps_list, interactive):
    pdf = matplotlib.backends.backend_pdf.PdfPages("output.pdf")
    for system_conf in system_confs:
        firstPage = plt.figure()
        firstPage.clf()
        txt = system_conf_fullname(system_conf)
        firstPage.text(0.5,0.5, txt, transform=firstPage.transFigure, size=14, ha="center")
        pdf.savefig(firstPage)
        plt.close()
        if system_conf['kernelconfig'] != 'disable_cstates':
            fig1 = plot_residency_per_target_qps(stats, system_conf, qps_list)
            pdf.savefig(fig1)
        fig2 = plot_total_qps_per_target_qps(stats, system_conf, qps_list)
        pdf.savefig(fig2)
        fig3 = plot_latency_per_target_qps(stats, system_conf, qps_list)
        pdf.savefig(fig3)
        fig4 = plot_power_per_target_qps(stats, system_conf, qps_list)
        pdf.savefig(fig4)
        if interactive:
            plt.show()
        plt.close(fig1)
        plt.close(fig2)
        plt.close(fig3)
        # plt.close(fig4)
    pdf.close()

def plot_stack(stats, system_confs, qps_list, interactive=True):
    pdf = matplotlib.backends.backend_pdf.PdfPages("all.pdf")
    for system_conf in system_confs:
        if system_conf['kernelconfig'] != 'disable_cstates':
            fig1 = plot_residency_per_target_qps(stats, system_conf, qps_list)
            pdf.savefig(fig1)
    fig2 = plot_total_qps_per_target_qps(stats, system_confs, qps_list)
    pdf.savefig(fig2)
    fig3 = plot_latency_per_target_qps(stats, system_confs, qps_list, filter = ['read_avg'])
    pdf.savefig(fig3)
    fig4 = plot_power_per_target_qps(stats, system_confs, qps_list)
    pdf.savefig(fig4)
    if interactive:
        plt.show()
    plt.close(fig2)
    plt.close(fig3)
    # plt.close(fig4)
    pdf.close()

def main(argv):
    stats_root_dir = argv[1]
    stats={}
    stats.setdefault(stats_root_dir, []).append(parse_single_instance_stats(stats_root_dir))
    write_csv_all(stats,stats_root_dir)

if __name__ == '__main__':
    main(sys.argv)
