DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS schema_meta;
CREATE TABLE schema_meta(version INTEGER NOT NULL);
CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE posts(id INTEGER PRIMARY KEY, title TEXT NOT NULL, user_ref TEXT NOT NULL);
INSERT INTO schema_meta(version) VALUES (2);
INSERT INTO users(id, name) VALUES (1, 'alice'), (2, 'bob');
INSERT INTO posts(id, title, user_ref) VALUES
  (1, 'draft', 'u:1'),
  (2, 'published', 'u:2'),
  (3, 'shared', 'u:2');
