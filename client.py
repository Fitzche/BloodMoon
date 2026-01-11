from kivy.app import App  # Classe de base pour créer une application Kivy
from kivy.uix.boxlayout import BoxLayout  # Conteneur qui aligne les widgets horizontalement ou verticalement
from kivy.uix.label import Label  # Pour afficher du texte
from kivy.uix.button import Button  # Pour créer des boutons cliquables
from kivy.uix.textinput import TextInput  # Pour entrer du texte (pseudo, chat, IP)
from kivy.uix.popup import Popup  # Pour créer des fenêtres popup
from kivy.clock import Clock  # Pour exécuter des fonctions sur le thread principal (UI)
from kivy.core.window import Window  # Pour gérer la fenêtre (taille, couleur de fond)
from kivy.graphics import Color, Rectangle  # Pour dessiner des couleurs et formes personnalisées

import socket  # Pour la communication réseau (client/serveur)
import json  # Pour envoyer/recevoir les données structurées
import threading  # Pour lancer le réseau en parallèle du GUI (pas bloquer l'interface)

# Définition des couleurs
# Chaque couleur est en RGBA, valeurs entre 0 et 1
COULEUR_FOND = (18/255, 18/255, 18/255, 1)       # Couleur principale du fond
COULEUR_PANEL = (25/255, 25/255, 25/255, 1)     # Fond des panneaux (sidebar)
COULEUR_INPUT = (35/255, 35/255, 35/255, 1)     # Fond des TextInput
COULEUR_TEXTE = (1, 1, 1, 1)  # Texte principal
COULEUR_TEXTE_FAIBLE = (1,0, 0, 1)  # Texte secondaire
COULEUR_ACCENT = (30/255, 215/255, 96/255, 1)   # Couleur accent (boutons, highlight)
COULEUR_DANGER = (220/255, 70/255, 70/255, 1)   # Couleur danger (mort, erreur)

Window.clearcolor = COULEUR_FOND  # Appliquer la couleur de fond globale


# Classe Panel : un BoxLayout avec couleur de fond personnalisée
class Panel(BoxLayout):
    def __init__(self, couleur, **kwargs):
        super().__init__(**kwargs)
        # On dessine un rectangle derrière le panel pour la couleur
        with self.canvas.before:
            Color(*couleur)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        # On met à jour le rectangle si le panel change de position ou taille
        self.bind(pos=self._mise_a_jour, size=self._mise_a_jour)

    def _mise_a_jour(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size

# Classe GameUI : interface de jeu (chat + sidebar)
class GameUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)

        self.votePop = None
        self.sock = None  # Socket réseau
        self.est_mort = False  # Flag pour savoir si le joueur est mort

        # Sidebar (liste des joueurs)
        self.sidebar = Panel(
            COULEUR_PANEL,
            orientation="vertical",
            size_hint_x=0.25,  # 25% largeur
            padding=12,
            spacing=10
        )

        # Titre de la sidebar
        self.sidebar.add_widget(Label(
            text="PLAYERS",
            font_size=13,
            color=COULEUR_TEXTE
        ))

        close_btn = Button(text="Choix", background_color=COULEUR_DANGER)
        close_btn.bind(on_release=lambda *_: self.showVotePopUp())




        # Label pour afficher la liste des joueurs
        self.players_label = Label(
            text="",
            color=COULEUR_TEXTE,
            halign="left",
            valign="top"
        )
        self.players_label.bind(size=self.players_label.setter("text_size"))
        self.sidebar.add_widget(self.players_label)
        self.sidebar.add_widget(close_btn)

        # Main (chat + input)
        self.main = Panel(
            COULEUR_FOND,
            orientation="vertical",
            padding=12,
            spacing=10
        )

        # Zone de chat (readonly)
        self.chat = Label(
            text="",
            markup=True,  # Permet d'utiliser des balises pour la couleur, taille
            color=COULEUR_TEXTE,
            halign="left",
            valign="top"
        )
        self.chat.bind(size=self.chat.setter("text_size"))
        self.main.add_widget(self.chat)

        # Zone d'entrée pour taper un message
        self.entry = TextInput(
            size_hint_y=0.12,
            background_color=COULEUR_INPUT,
            foreground_color=COULEUR_TEXTE,
            cursor_color=COULEUR_ACCENT,
            multiline=False,
            hint_text="Message"
        )
        self.entry.bind(on_text_validate=self.send_chat)  # Envoi au Enter
        self.main.add_widget(self.entry)

        # Ajout des panels à l'UI
        self.add_widget(self.sidebar)
        self.add_widget(self.main)



    # Fonctions d'affichage
    def log(self, texte, couleur=COULEUR_TEXTE, taille=14):
        """Ajouter un message dans le chat"""

        r = int(couleur[0] * 255)
        g = int(couleur[1] * 255)
        b = int(couleur[2] * 255)
        hex_color = f"{r:02X}{g:02X}{b:02X}"


        self.chat.text += (
            f"\n[size={taille}]"
            f"[color=#{hex_color}]"
            f"{texte}"
            f"[/color][/size]"
        )

    def set_players(self, liste_joueurs):
        """Mettre à jour la sidebar des joueurs"""
        self.players_label.text = "\n".join(liste_joueurs)

    # Réseau : connexion au serveur
    def connect(self, ip, pseudo):
        """Se connecter au serveur avec l'IP et pseudo"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, 5555))
        self.sock.send(json.dumps({"name": pseudo}).encode())

        # Lancer l'écoute des messages en parallèle
        threading.Thread(target=self.listen, daemon=True).start()
        self.log("Connected to server", COULEUR_TEXTE_FAIBLE)



    def handle(self, msg):
        """Traiter les messages reçus"""
        print("handle message")
        action = msg.get("action")

        if action == "chat":

            print("has message: ", msg.get('content',''))

            dest = ""
            color = COULEUR_TEXTE



            if msg.get('isSystem', False):
                print("from system")
                dest = "SYS"

            else:
                print("not from system")
                dest = msg.get('fromPlayer','SYS')

            if dest == "" or dest == '':
                dest = "SYS"

            if dest == "SYS" or dest == 'SYS':
                color = COULEUR_TEXTE_FAIBLE
            self.log(f"{dest} : {msg.get('content','')}", color)

        elif action == "players":
            print("players list given")
            self.set_players(msg.get("list", []))

        elif action == "role":
            self.show_role(msg.get("role", "Unknown"), msg.get("description", ""))

        elif action == "phase":
            if msg.get("value") == "night":
                Window.clearcolor = COULEUR_PANEL
                self.log("Night phase", COULEUR_TEXTE_FAIBLE)
            else:
                Window.clearcolor = COULEUR_FOND
                self.log("Day phase", COULEUR_TEXTE_FAIBLE)

        elif action == "choice" and not self.est_mort:
            self.vote_popup(msg)

        elif action == "death":
            self.est_mort = True
            self.log("YOU ARE DEAD", COULEUR_DANGER, 18)

        elif action == "end":
            self.end_popup(msg.get("winner"))



    def listen(self):

        buffer = "" #on crée un buffer pour stocker les morceaux de messages
        while True:
            try:
                data = self.sock.recv(2048).decode('utf-8')
                if not data: break

                buffer += data #on ajoute au buffer

                #on découpe le buffer à chaque retour à la ligne
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip(): #si la ligne n'est pas vide
                        msg = json.loads(line)
                        print("Value loaded successfully")
                        Clock.schedule_once(lambda dt, m=msg: self.handle(m))

            except Exception as e:
                print(f"Erreur listen: {e}")
                break




    # Actions utilisateur
    def send_chat(self, *_):
        """Envoyer un message chat au serveur"""
        if not self.sock:
            return
        txt = self.entry.text.strip()
        if not txt:
            return
        self.entry.text = ""
        self.sock.send(json.dumps({
            "action": "chat",
            "content": txt
        }).encode())

    def vote_popup(self, msg):

        #en fonction du type de la liste, les choix varient
        if msg.get("type", 1) == 1:
            listOfChoices = self.players_label.text.split("\n")
        elif msg.get("type", 1) == 2:
            listOfChoices = msg.get("choices", [])
        elif msg.get("type", 1):
            listOfChoices = ["Oui", "Non"]
        else:
            listOfChoices = ["ErreurChoice1", "ErreurChoice2"]
        """Afficher une popup pour faire un choix"""
        box = Panel(COULEUR_PANEL, orientation="vertical", padding=15, spacing=10)
        box.add_widget(Label(text=msg.get("instruct", "Vote"), color=COULEUR_TEXTE))

        #on ajoute un bouton pour chaque choix possibles
        for p in listOfChoices:
            if not p:
                continue
            b = Button(text=p, background_color=COULEUR_INPUT, color=COULEUR_TEXTE)
            b.bind(on_release=lambda _, n=p: self.send_vote(msg.get("id"), n))
            box.add_widget(b)

        #on ajoute un bouton pour fermer la popup
        close_btn = Button(text="Fermer", background_color=COULEUR_DANGER)
        close_btn.bind(on_release=lambda *_:self.hide_vote_popup())
        box.add_widget(close_btn)

        #on stocke les valeurs de la popup dans une variable pour pouvoir la rouvrir si besoin
        self.votePop = Popup(title="Choice", content=box, size_hint=(0.45, 0.65))

        #on ouvre la popup de choix
        self.votePop.open()


    #fonction pour ouvrir la popup de choix
    def showVotePopUp(self):

        #on vérifie si la popup de choix existe avant de l'ouvrir
        if not self.votePop == None:

            self.votePop.open()


     #fonction pour fermer la popup de choix
    def hide_vote_popup(self):
        # on vérifie si la popup de choix existe avant de la fermer
        if not self.votePop == None:
            self.votePop.dismiss()

    def send_vote(self, pcid, ans):
        """Envoyer le choix de vote au serveur"""
        self.log("Vous avez choisi: "+ ans, COULEUR_TEXTE_FAIBLE)
        self.sock.send(json.dumps({
            "action": "choiceAnswer",
            "id": pcid,
            "answer": ans
        }).encode())



    # Popups d'information
    def show_role(self, role, desc):
        """Afficher le rôle du joueur"""
        box = Panel(COULEUR_PANEL, orientation="vertical", padding=20, spacing=10)
        box.add_widget(Label(text=role, font_size=22, color=COULEUR_ACCENT))
        box.add_widget(Label(text=desc, color=COULEUR_TEXTE))
        Popup(title="Your role", content=box, size_hint=(0.6, 0.6)).open()

    def end_popup(self, winner):
        """Afficher la fin de la partie"""
        txt = "VICTORY" if winner == "you" else "DEFEAT"
        lbl = Label(text=txt, font_size=38, color=COULEUR_ACCENT)
        Popup(title="Game Over", content=lbl, size_hint=(0.5, 0.4)).open()

# Classe principale de l'application GUI
class GUI(App):
    def build(self):
        root = BoxLayout(orientation="vertical")

        # ===== Barre en haut : IP + Username + Connect =====
        top = Panel(COULEUR_PANEL, size_hint_y=0.12, padding=10, spacing=10)

        self.ip_input = TextInput(hint_text="IP", background_color=COULEUR_INPUT, foreground_color=COULEUR_TEXTE, multiline=False)
        self.username_input = TextInput(hint_text="Username", background_color=COULEUR_INPUT, foreground_color=COULEUR_TEXTE, multiline=False)
        btn = Button(text="CONNECT", background_color=COULEUR_ACCENT, color=(0, 0, 0, 1))
        btn.bind(on_release=self.start_game)  # Appuyer sur Connect lance la partie





        top.add_widget(self.ip_input)
        top.add_widget(self.username_input)
        top.add_widget(btn)

        # ===== Zone principale de jeu =====
        self.game = GameUI()
        root.add_widget(top)
        root.add_widget(self.game)

        return root

    def start_game(self, *_):
        """Connecter le joueur au serveur"""
        self.game.connect(
            self.ip_input.text.strip(),
            self.username_input.text.strip()
        )

# Lancer l'application
GUI().run()
