![logo](https://github.com/jannis15/eSports-Calendar/assets/78983365/bc11637b-f357-497c-baa2-407821411c35)

Der eSports-Kalender ist ein Hobby-Projekt zur Verwaltung von Terminen eines Sportvereins. Die Grundidee besteht darin, dass Spieler ihre verfügbaren Zeitfenster in einem Kalender eintragen können, sodass die Team-Kapitäne einen besseren Überblick darüber erhalten, wann sie am besten Termine für Ligaspiele und andere Veranstaltungen planen können. 

Die Motivation für dieses Projekt entstand aus den Schwierigkeiten eines mir bekannten Vereinskapitäns. Er hatte Probleme damit, Termine für kommende Spiele vorzuschlagen, da er nicht wusste, wann seine Spieler während der Woche Zeit hatten. Daraufhin entwickelte ich eine Webplattform, welches diese Problematik in Angriff nehmen sollte.

# Die Kalenderansicht

![calendar](https://github.com/jannis15/eSports-Calendar/assets/78983365/13254e90-be97-408a-a666-1a0b42b70aa4)

Die Kalenderansicht ist das Kernstück der Webseite. Hier befinden sich alle Terminzeitfenster auf einem Blick. Hier können Spieler und Kapitäne die Termine einsehen und bearbeiten.

- Termin bearbeiten:

  ![termin_bearbeiten](https://github.com/jannis15/eSports-Calendar/assets/78983365/0029d9ec-9ea2-4a9b-afd5-33bf5b8e2c3a)

# Tech-Stack

![techstack](https://github.com/jannis15/eSports-Calendar/assets/78983365/44e96d5d-ba22-4377-aae0-c959e3615b46)
![techstac_frontendk](https://github.com/jannis15/eSports-Calendar/assets/78983365/9d61099f-8c44-4740-9b49-52e7aa694987)

Python wurde als Backend-Sprache gewählt, da sich mit dem FastAPI-Framework REST-APIs mit Benutzerauthentifizierung einfach erstellen lassen. Zusätzlich verwendete ich das SQLAlchemy-Framework, um relationale Datenbanktabellen mit Python-Objekten zu verknüpfen und das Schreiben von SQL-Queries zu vereinfachen. 

Für das Frontend verwendete ich serverseitiges Rendering durch Jinja2-Templates. Um Antworten an das Backend zurückzuschicken, nutzte ich JQuery.

# Planung


Das folgende ERM zeigt die Kern-Entitätstypen der Datenbank. Es zeigt, wie ein Spieler (oder Anwender) einem bestimmten Team einer Organisation zugeordnet werden kann. Zugleich zeigt das Modell wie die Kalendertermine zwischen Spieler-Termin und Team-Termin unterscheidet. Ein Termin wurde in verschiedenen Tabellen aufgeteilt, um zukünftig neue Eigenschaften speziell einem Spieler-Termin oder einem Team-Termin zuordnen zu können. Eine Termin-Priorität kann zum Beispiel nur bei einem Spieler-Termin gesetzt werden. Die Sitzungstabelle speichert den Sitzungsverlauf eines Spielers. Er wird genutzt um den Anwender anhand eines Sitzungsschlüssel automatisch einzuloggen. Der Sitzungsschlüssel läuft nach einer Woche ab, sofern die Webseite innerhalb des Zeitraums nicht wieder besucht wurde.

![image](https://github.com/jannis15/eSports-Calendar/assets/78983365/b8b29ddd-0b38-4f9a-9332-f001e42068f5)

## Desing-Mockups

![Figma-1-logo](https://github.com/jannis15/eSports-Calendar/assets/78983365/e0832d8b-66b3-4450-9c56-ae2c00e18ca5)

Für die Planung die Organisationsseite verwendete ich Figma, um das Design zu konzipieren. Dies half mir dabei, das Layout schneller in der Entwicklung umzusetzen.

- Prototyp für eine Organisationsseite:

![org_concept](https://github.com/jannis15/eSports-Calendar/assets/78983365/263cd46c-c3be-44da-ab8b-cc52109ac8cc)

# Weitere Ansichten:

- Organisation:

![org_details](https://github.com/jannis15/eSports-Calendar/assets/78983365/ad0f3f9c-67a6-4053-9252-c7ce1ac1cb02)

- Team:

![team_details](https://github.com/jannis15/eSports-Calendar/assets/78983365/8a5b73e7-26d0-4ef5-8c92-18e664670a87)


- Login & Registrierung:

![login](https://github.com/jannis15/eSports-Calendar/assets/78983365/9b9e6576-8adf-4660-ae7c-806edb49409d)

![signup](https://github.com/jannis15/eSports-Calendar/assets/78983365/1049876e-6d15-401d-8254-c20690821e56)

- Dashboard & Einladungslink:

![dashboard](https://github.com/jannis15/eSports-Calendar/assets/78983365/bf30b015-3d3c-4090-8de3-8a2eef7e4d0c)

![invitation](https://github.com/jannis15/eSports-Calendar/assets/78983365/420a71b5-7823-4d2b-83bd-ec56e87e16f1)
