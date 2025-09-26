PRAGMA foreign_keys = ON;

CREATE TABLE users(
    username VARCHAR(20) NOT NULL,
    fullname VARCHAR(40) NOT NULL,
    email VARCHAR(40) NOT NULL,
    filename VARCHAR(64) NOT NULL,
    password VARCHAR(256) NOT NULL,
    created  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(username)
);

CREATE TABLE posts (
    postid   INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(64),
    owner    VARCHAR(20),
    created  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE following (
    follower VARCHAR(20),
    followee VARCHAR(20),
    created  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower, followee),
    FOREIGN KEY (follower) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (followee) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE comments (
    commentid INTEGER PRIMARY KEY AUTOINCREMENT,
    owner     VARCHAR(20),
    postid    INTEGER,
    text      VARCHAR(1024),
    created   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (postid) REFERENCES posts(postid) ON DELETE CASCADE
);

CREATE TABLE likes (
    likeid  INTEGER PRIMARY KEY AUTOINCREMENT,
    owner   VARCHAR(20),
    postid  INTEGER,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (postid) REFERENCES posts(postid) ON DELETE CASCADE,
    UNIQUE(owner, postid)
);