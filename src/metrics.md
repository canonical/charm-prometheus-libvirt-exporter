# List of metrics collected by prometheus-libvirt-exporter snap
* libvirt_domain_block_stats_read_bytes_total Number of bytes read from a block device, in bytes.
* libvirt_domain_block_stats_read_requests_total Number of read requests from a block device.
* libvirt_domain_block_stats_write_bytes_total Number of bytes written to a block device, in bytes.
* libvirt_domain_block_stats_write_requests_total Number of write requests to a block device.
* libvirt_domain_info_cpu_time_seconds_total Amount of CPU time used by the domain, in seconds.
* libvirt_domain_info_maximum_memory_bytes Maximum allowed memory of the domain, in bytes.
* libvirt_domain_info_memory_usage_bytes Memory usage of the domain, in bytes.
* libvirt_domain_info_virtual_cpus Number of virtual CPUs for the domain.
* libvirt_domain_interface_stats_receive_bytes_total Number of bytes received on a network interface, in bytes.
* libvirt_domain_interface_stats_receive_drops_total Number of packet receive drops on a network interface.
* libvirt_domain_interface_stats_receive_errors_total Number of packet receive errors on a network interface.
* libvirt_domain_interface_stats_receive_packets_total Number of packets received on a network interface.
* libvirt_domain_interface_stats_transmit_bytes_total Number of bytes transmitted on a network interface, in bytes.
* libvirt_domain_interface_stats_transmit_drops_total Number of packet transmit drops on a network interface.
* libvirt_domain_interface_stats_transmit_errors_total Number of packet transmit errors on a network interface.
* libvirt_domain_interface_stats_transmit_packets_total Number of packets transmitted on a network interface.
* libvirt_up Whether scraping libvirt's metrics was successful.

### Also available starting from v2.3.0+
* libvirt_domain_block_meta Block device metadata info. Device name, source file, serial.
* libvirt_domain_block_stats_allocation Offset of the highest written sector on a block device.
* libvirt_domain_block_stats_capacity_bytes Logical size in bytes of the block device	backing image.
* libvirt_domain_block_stats_flush_requests_total Total flush requests from a block device.
* libvirt_domain_block_stats_flush_time_seconds_total Total time in seconds spent on cache flushing to a block device
* libvirt_domain_block_stats_limit_burst_length_read_requests_seconds Read requests per second burst time in seconds
* libvirt_domain_block_stats_limit_burst_length_total_requests_seconds Total requests per second burst time in seconds
* libvirt_domain_block_stats_limit_burst_length_write_requests_seconds Write requests per second burst time in seconds
* libvirt_domain_block_stats_limit_burst_read_bytes Read throughput burst limit in bytes per second
* libvirt_domain_block_stats_limit_burst_read_bytes_length_seconds Read throughput burst time in seconds
* libvirt_domain_block_stats_limit_burst_read_requests Read requests per second burst limit
* libvirt_domain_block_stats_limit_burst_total_bytes Total throughput burst limit in bytes per second
* libvirt_domain_block_stats_limit_burst_total_bytes_length_seconds Total throughput burst time in seconds
* libvirt_domain_block_stats_limit_burst_total_requests Total requests per second burst limit
* libvirt_domain_block_stats_limit_burst_write_bytes Write throughput burst limit in bytes per second
* libvirt_domain_block_stats_limit_burst_write_bytes_length_seconds Write throughput burst time in seconds
* libvirt_domain_block_stats_limit_burst_write_requests Write requests per second burst limit
* libvirt_domain_block_stats_limit_read_bytes Read throughput limit in bytes per second
* libvirt_domain_block_stats_limit_read_requests Read requests per second limit
* libvirt_domain_block_stats_limit_total_bytes Total throughput limit in bytes per second
* libvirt_domain_block_stats_limit_total_requests Total requests per second limit
* libvirt_domain_block_stats_limit_write_bytes Write throughput limit in bytes per second
* libvirt_domain_block_stats_limit_write_requests Write requests per second limit
* libvirt_domain_block_stats_physicalsize_bytes Physical size in bytes of the container of the backing image.
* libvirt_domain_block_stats_read_time_seconds_total Total time spent on reads from a block device, in seconds.
* libvirt_domain_block_stats_size_iops_bytes The size of IO operations per second permitted through a block device
* libvirt_domain_block_stats_write_time_seconds_total Total time spent on writes on a block device, in seconds
* libvirt_domain_info_meta Domain metadata. Domain, flavor, instance_name, project_name, project_uuid, root_type, root_uuid, user_name, user_uuid, uuid.
* libvirt_domain_info_vstate Virtual domain state. 0: no state, 1: the domain is running, 2: the domain is blocked on resource, 3: the domain is paused by user, 4: the domain is being shut down, 5: the domain is shut off,6: the domain is crashed, 7: the domain is suspended by guest power management
* libvirt_domain_interface_meta Interfaces metadata. Source bridge, target device, interface uuid
* libvirt_domain_memory_stats_actual_balloon_bytes Current balloon value (in bytes).
* libvirt_domain_memory_stats_available_bytes The total amount of usable memory as seen by the domain. This value may be less than the amount of memory assigned to the domain if a balloon driver is in use or if the guest OS does not initialize all assigned pages. This value is expressed in bytes.
* libvirt_domain_memory_stats_disk_cache_bytes The amount of memory, that can be quickly reclaimed without additional I/O (in bytes).Typically these pages are used for caching files from disk.
* libvirt_domain_memory_stats_major_fault_total Page faults occur when a process makes a valid access to virtual memory that is not available. When servicing the page fault, if disk IO is required, it is considered a major fault.
* libvirt_domain_memory_stats_minor_fault_total Page faults occur when a process makes a valid access to virtual memory that is not available. When servicing the page not fault, if disk IO is required, it is considered a minor fault.
* libvirt_domain_memory_stats_rss_bytes Resident Set Size of the process running the domain. This value is in bytes
* libvirt_domain_memory_stats_unused_bytes The amount of memory left completely unused by the system. Memory that is available but used for reclaimable caches should NOT be reported as free. This value is expressed in bytes.
* libvirt_domain_memory_stats_usable_bytes How much the balloon can be inflated without pushing the guest system to swap, corresponds to 'Available' in /proc/meminfo
* libvirt_domain_memory_stats_used_percent The amount of memory in percent, that used by domain.
* libvirt_domain_vcpu_cpu Real CPU number, or one of the values from virVcpuHostCpuState
* libvirt_domain_vcpu_state VCPU state. 0: offline, 1: running, 2: blocked
* libvirt_domain_vcpu_time_seconds_total Amount of CPU time used by the domain's VCPU, in seconds.
* libvirt_domain_vcpu_wait_seconds_total Vcpu's wait_sum metric. CONFIG_SCHEDSTATS has to be enabled
* libvirt_versions_info Versions of virtualization components
