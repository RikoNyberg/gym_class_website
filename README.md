# gym_class_website

This is the front end of the gym_class_booking service and it is running on top of Heroku.

Check out the example website from https://gym-class.herokuapp.com/test
:)

## Run
Instructions on how to setup https and nginx-proxy for this website:
https://medium.com/@francoisromain/host-multiple-websites-with-https-inside-docker-containers-on-a-single-server-18467484ab95

First you have to create a Nginx-proxy to your server for conrolling the traffic ([simple instruction here](https://medium.com/@francoisromain/host-multiple-websites-with-https-inside-docker-containers-on-a-single-server-18467484ab95)). After that you can dowload the app to your server and run the following commands inside the website folder.
```
$ cd .../gym_class_website

$ docker build -t gym_class_website .

$ docker-compose up -d
```