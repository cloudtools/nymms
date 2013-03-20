import nanomon
from nanomon import registry


webserver_group = nanomon.MonitoringGroup('webservers', port=80)
www1 = nanomon.Host('www1', monitoring_groups=[webserver_group,], port=443, type='m1.xlarge')
http_check = nanomon.Command('check_http',
        'check_http {host:address} {port}', port=80)
http_monitor = nanomon.Monitor('http_monitor', command=http_check, monitoring_groups=[webserver_group,])
