-- $ sqlite3 users.db < users.sql

PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS followers;
CREATE TABLE users (
    id INTEGER primary key,
    username VARCHAR,
    password VARCHAR,
    emailAddress VARCHAR,
    UNIQUE(username, emailAddress)
);
CREATE TABLE followers (
    id INTEGER primary key,
    username VARCHAR,
    userToFollow VARCHAR
);
INSERT INTO users(username, password, emailAddress) VALUES('admin', 'admin', 'admin@gmail.com');
INSERT INTO users(username, password, emailAddress) VALUES('henry', 'henry', 'henry@gmail.com');
INSERT INTO users(username, password, emailAddress) VALUES('calvin', 'calvin', 'calvin@gmail.com');
INSERT INTO users(username, password, emailAddress) VALUES('tommy', 'tommy', 'tommy@gmail.com');
INSERT INTO users(username, password, emailAddress) VALUES('test', 'test', 'test@gmail.com');

INSERT INTO followers(username, userToFollow) VALUES('test', 'admin');
INSERT INTO followers(username, userToFollow) VALUES('calvin', 'test');
INSERT INTO followers(username, userToFollow) VALUES('henry', 'test');
INSERT INTO followers(username, userToFollow) VALUES('admin', 'calvin');
INSERT INTO followers(username, userToFollow) VALUES('henry', 'admin');
INSERT INTO followers(username, userToFollow) VALUES('henry', 'calvin');
INSERT INTO followers(username, userToFollow) VALUES('henry', 'tommy');

COMMIT;
