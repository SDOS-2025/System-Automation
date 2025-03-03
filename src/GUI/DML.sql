-- DML
CREATE TABLE IF NOT EXISTS settings (
    id INT NOT NULL UNIQUE,
	key TEXT,
	sensVal DECIMAL(2, 1),
    PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS history (
	id INT NOT NULL UNIQUE,
	time TIMESTAMP,
	input TEXT,
	PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS screenshots(
	id INT NOT NULL UNIQUE,
	historyID INT,
	BLOB ss,
	PRIMARY KEY(id),
	FOREIGN KEY (historyID) REFERENCES history(id)
	
);

CREATE TABLE IF NOT EXISTS presets(
	id INT NOT NULL UNIQUE,
	PRIMARY KEY(id),
	presetName TEXT UNIQUE,
	commands TEXT
);

--DCL
-- Fetch Settings row
FROM SETTINGS SELECT *

-- Default Settings
INSERT INTO settings (key, sensVal) VALUES ("", 0.5);

--Updating Settings
UPDATE 