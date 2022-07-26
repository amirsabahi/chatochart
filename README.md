# Requirements
pip3.10 install Django 4^
pip3.10 install djangorestframework
pip3.10 install PIL-Tools
pip3.10 install django-autoslug
pip3.10 install django-cors-headers
pip3.10 install requests
pip3.10 install celery

---
# Queue Management
 How to install RabbitQM on the server CentOS7:
 https://www.vultr.com/docs/how-to-install-rabbitmq-on-centos-7/
 https://stackoverflow.com/a/45475646/558547

 Access to panel: http://185.110.189.32:15672/

Run Celery:
First go to the environment and activate it. Then run
celery -A social worker --loglevel=info -B
Supervisord is used. Follow this instruction:
https://realpython.com/asynchronous-tasks-with-django-and-celery/
s
---
# Search 
https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html
** Install `Elastic search` Django **
https://django-elasticsearch-dsl.readthedocs.io/en/latest/quickstart.html
`pip install django-elasticsearch-dsl`

---

--- 
# Commenting System
Creating hierarchical commenting system:
http://mikehillyer.com/articles/managing-hierarchical-data-in-mysql/
https://www.waitingforcode.com/mysql/managing-hierarchical-data-in-mysql-nested-set/read

# MongoDB
If later we need to work with MongoDB:
For Database follow the link here:
https://www.mongodb.com/compatibility/mongodb-and-django
Install app packages including:  mongoengine, dnspython, djongo