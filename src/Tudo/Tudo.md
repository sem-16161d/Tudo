***Important***

windows: https://w3resource.com/PostgreSQL/install-postgresql-on-linux-and-windows.php

**how to install postgres for usage with tudo on mac:**

bash:
    brew install postgresql
    brew services start postgresql@18

    brew services stop postgresql (to end)

*restart terminal*

bash:
    psql postgres 

should start the psql

\q [Enter] to quit psql

*make a new database cluster*
go to the folder where you want the database
bash:
    initdb -D .
    pg_ctl -D . start  (if not already runnig)
    pg_ctl -D . stop

*new Database*
bash:
    createdb mydb

*access it*
bash:
    psql mydb

https://www.postgresql.org/docs/18/tutorial-table.html
