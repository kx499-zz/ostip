PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

ALTER TABLE indicator RENAME TO old_indicator;

CREATE TABLE indicator (
	id INTEGER NOT NULL,
	ioc VARCHAR(64) NOT NULL,
	comment VARCHAR(255),
	enrich VARCHAR(255),
	first_seen DATETIME NOT NULL,
	last_seen DATETIME NOT NULL,
	pending BOOLEAN NOT NULL,
	event_id INTEGER NOT NULL,
	control_id INTEGER NOT NULL,
	itype_id INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (ioc, event_id, itype_id, control_id),
	CHECK (pending IN (0, 1)),
	FOREIGN KEY(event_id) REFERENCES event (id),
	FOREIGN KEY(control_id) REFERENCES control (id),
	FOREIGN KEY(itype_id) REFERENCES itype (id)
);

INSERT INTO indicator SELECT * FROM old_indicator;

COMMIT;

PRAGMA foreign_keys=on;