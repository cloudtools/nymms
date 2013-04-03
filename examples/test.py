from nymms import resources

import logging
logging.basicConfig(level=logging.DEBUG)


webserver_group = resources.MonitoringGroup('webservers', port=80)
www1 = resources.Node('www1', monitoring_groups=[webserver_group,], port=443, type='m1.xlarge')
http_check = resources.Command('check_http',
        'check_http {host[address]} {port}', port=80)
http_monitor = resources.Monitor('http_monitor', command=http_check, monitoring_groups=[webserver_group,])
