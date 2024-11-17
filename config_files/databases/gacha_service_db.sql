DROP DATABASE IF EXISTS GachaService;

CREATE DATABASE GachaService;
USE GachaService;

DROP TABLE IF EXISTS Collection;
DROP TABLE IF EXISTS Gacha;


CREATE TABLE Gacha (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    id_img VARCHAR(100),
    rarity ENUM('Common','Uncommon', 'Rare', 'Super Rare', 'Legendary') NOT NULL
);


CREATE TABLE Collection (
    user_id INT, -- user_id è un riferimento esterno al microservizio User
    gacha_id INT,
    quantity INT DEFAULT 1,
    PRIMARY KEY (user_id, gacha_id),
    FOREIGN KEY (gacha_id) REFERENCES Gacha(id) ON DELETE CASCADE
);


INSERT INTO Gacha (name, description, id_img, rarity) VALUES
('Abu', 'A mischievous and clever monkey who is fiercely loyal to Aladdin, often getting into trouble but always helping his friend out of tight spots. (Aladdin)', 'abu', 'Common'),
('Donald Duck', 'A classic character known for his distinct voice, quick temper, and humorous personality, Donald is a determined and resilient duck who often gets into comical situations. (Various)', 'donald_duck', 'Common'),
('Goofy', 'A lovable, clumsy dog with a big heart and an optimistic outlook; Goofy’s goofy personality and infectious laugh make him a memorable and endearing friend. (Various)', 'goofy', 'Common'),
('Magic Broom', 'An enchanted broom brought to life by a magical spell, it tirelessly carries water buckets and creates chaos in the process, symbolizing the consequences of magic gone wrong. (Fantasia)', 'magic_broom', 'Common'),
('Pongo', 'A caring and resourceful dalmatian who, along with his mate Perdita, goes to great lengths to rescue his stolen puppies, showing deep love and courage. (101 Dalmatians)', 'pongo', 'Common'),
('Stitch', 'A wild, chaotic alien experiment who finds love and belonging with Lilo, eventually learning about family and loyalty despite his mischievous nature. (Lilo & Stitch)', 'stitch', 'Common'),
('Timon', 'A sarcastic and witty meerkat who, with his best friend Pumbaa, lives by the motto “Hakuna Matata,” embracing a carefree lifestyle but showing bravery when it matters most. (The Lion King)', 'timon', 'Common'),
('Yzma', 'A power-hungry, eccentric villain with a knack for potions and a dark sense of humor, Yzma plots to take over the empire through comical and ruthless schemes. (The Emperor\'s New Groove)', 'yzma', 'Common'),
('Mufasa', 'A majestic, wise, and courageous lion king who deeply loves his son Simba and teaches him important values, leaving a lasting legacy. (The Lion King)', 'mufasa', 'Legendary'),
('Scar', 'A cunning, manipulative lion with a smooth-talking demeanor, Scar is willing to do anything to claim the throne, making him a formidable antagonist. (The Lion King)', 'scar', 'Rare'),
('Jasmine', 'A spirited and independent princess who yearns for freedom and adventure beyond the palace walls, finding love and courage along the way. (Aladdin)', 'jasmine', 'Rare'),
('Kuzco', 'A spoiled, selfish emperor who learns humility and kindness after being transformed into a llama, leading to a journey of self-discovery. (The Emperor\'s New Groove)', 'kuzco', 'Rare'),
('Maui', 'A larger-than-life demigod with shape-shifting powers, Maui is both proud and humorous, eventually showing his heroic side as he aids Moana in her quest. (Moana)', 'maui', 'Rare'),
('Lilo', 'A quirky, imaginative young girl with a deep sense of compassion, who befriends and tames Stitch, teaching him the meaning of family. (Lilo & Stitch)', 'lilo', 'Super Rare'),
('Peter Pan', 'A charismatic and adventurous boy who refuses to grow up, leading the Lost Boys and bringing a sense of wonder and bravery to Neverland. (Peter Pan)', 'peter_pan', 'Super Rare'),
('Sisu', 'A kind, eccentric dragon with the power to bring rain, Sisu is both wise and selfless, joining Raya on a mission to unite their fractured world. (Raya and the Last Dragon)', 'sisu', 'Super Rare'),
('Flynn Rider', 'A charming thief with a roguish personality, Flynn starts off self-centered but transforms as he falls for Rapunzel and discovers his true worth. (Tangled)', 'flynn_rider', 'Uncommon'),
('Rafiki', 'A wise and mystical baboon who serves as a guide to Simba, offering spiritual wisdom and comic relief through his unique insights. (The Lion King)', 'rafiki', 'Uncommon'),
('Simba', 'A lion who faces the loss of his father and ultimately embraces his destiny to become king, learning courage and responsibility along the way. (The Lion King)', 'simba', 'Uncommon'),
('Sven', 'A loyal and gentle reindeer with a playful side, Sven is devoted to his best friend Kristoff, often providing silent yet comedic support. (Frozen)', 'sven', 'Uncommon');

