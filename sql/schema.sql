CREATE TABLE games (
    id INT PRIMARY KEY,
    stadium VARCHAR(255),
    date DATE,
    home_team VARCHAR(255),
    visitor_team VARCHAR(255)
);

CREATE TABLE at_bat (
    id INT PRIMARY KEY AUTO_INCREMENT,
    game_id INT,
    inning INT,
    batter VARCHAR(255),
    pitcher VARCHAR(255)
);

CREATE TABLE pitches (
    id INT PRIMARY KEY AUTO_INCREMENT,

    at_bat_id INT,

    inning INT,
    number_of_pitches INT,
    pitch_number INT,

    pitcher VARCHAR(255),
    pitcher_team VARCHAR(255),

    batter VARCHAR(255),
    batter_team VARCHAR(255),

    pitch_type VARCHAR(255),
    speed INT,

    ball INT,
    strike INT,
    outs INT,

    result VARCHAR(255),

    x FLOAT,
    y FLOAT,

    first INT,
    second INT,
    third INT
);