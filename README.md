# chopine
A small REST-api msg-server in bottle

### Synopsis

En meddelandetjänst, med vilken man kan skicka textmeddelanden till
mottagare och läsa dessa som mottagare. Man kan

1. Skicka meddelande till en mottagare, identifierad med epostadress,
telefonnummer eller användarnamn.

2. Hämta nya (sedan förra hämtningen) meddelanden till mottagare

3. Ta bort ett eller flera meddelanden för en mottagare

4. Hämta tidsordnade meddelanden till en mottagare enligt start och stopp index

Implementationen har ett REST-API

### Credits

The server is based on the python web-framework [bottle](https://github.com/bottlepy/bottle).
The file bottle.py is copied verbatim from them.

### Usage instructions 

install on macosx:
```
  > sudo easy_install pip
  > pip install webtest 
```

Start server:
```
    ./chopine.py <port>
```
Run Tests:
```
    ./chopine.py
```

Add a user:
```
    curl -d "user=pelle&phone=456&email=pelle@uppsala" http://localhost:8080/add_new_user
```

List Users ([try me!](http://localhost:8080/users)):
```
    curl http://localhost:8080/users
```

Dump a user's info:
```
    curl http://localhost:8080/users/pelle
```

Add a message:
```
    curl -d "to=foo&from=ara&msg=hello world." http://localhost:8080/add_msg
```

Delete some messages:
```
    curl  http://localhost:8080/msgs/pelle?id=1,3
```

Fetch messages:
```
    curl  http://localhost:8080/msgs/pelle
    curl  http://localhost:8080/msgs/pelle?lb=3
    curl  http://localhost:8080/msgs/pelle?lb=2&ub=3
```

Fetch new messages:
```
    curl  http://localhost:8080/msgs/pelle?new
```
