# -*- coding: utf-8 -*-
#
# This file is part of the Mage Knight implementation at
# https://github.com/MartinAltmayer/mageknight.
#
# Copyright 2015 Martin Altmayer, Stefan Altmayer
# The Mage Knight board game was created by Vlaada Chvátil.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from mageknight import utils

CARDS = {}
CARDS['sites'] = [
    'mk/cards/sites/ancient_ruins.png',
    'mk/cards/sites/city.png', 
    'mk/cards/sites/draconum.png',
    'mk/cards/sites/dungeon.png',
    'mk/cards/sites/keep.png',
    'mk/cards/sites/mage_tower.png',
    'mk/cards/sites/marauding_orcs.png',
    'mk/cards/sites/mines_glades.png',
    'mk/cards/sites/monastery.png',
    'mk/cards/sites/monster_den.png',
    'mk/cards/sites/spawning_grounds.png',
    'mk/cards/sites/tomb.png',  
    'mk/cards/sites/village.png',    
]

CARDS['skills'] = [
    'mk/cards/skills/arythea.png',
    'mk/cards/skills/goldyx.png',
    'mk/cards/skills/norowas.png',
    'mk/cards/skills/tovak.png',
]

CARDS['cities'] = [
    'mk/cards/cities/blue.png',
    'mk/cards/cities/blue_difficulty.png',
    'mk/cards/cities/green.png',
    'mk/cards/cities/green_difficulty.png',
    'mk/cards/cities/red.png',
    'mk/cards/cities/red_difficulty.png',
    'mk/cards/cities/white.png',  
    'mk/cards/cities/white_difficulty.png',                  
]

CARDS['tactics_day'] = ['mk/cards/tactics/d{}.jpg'.format(i) for i in range(1,7)]
CARDS['tactics_night'] = ['mk/cards/tactics/n{}.jpg'.format(i) for i in range(1,7)]
 
CARDS['basic_actions'] = [
    'mk/cards/basic_actions/battle_versatility.jpg',
    'mk/cards/basic_actions/cold_toughness.jpg',  
    'mk/cards/basic_actions/concentration.jpg', 
    'mk/cards/basic_actions/crystallize.jpg',
    'mk/cards/basic_actions/determination.jpg',
    'mk/cards/basic_actions/improvisation.jpg',
    'mk/cards/basic_actions/mana_draw.jpg',
    'mk/cards/basic_actions/march.jpg',
    'mk/cards/basic_actions/noble_manners.jpg',
    'mk/cards/basic_actions/promise.jpg',
    'mk/cards/basic_actions/rage.jpg',
    'mk/cards/basic_actions/stamina.jpg',
    'mk/cards/basic_actions/swiftness.jpg',
    'mk/cards/basic_actions/threaten.jpg',
    'mk/cards/basic_actions/tranquility.jpg',
    'mk/cards/basic_actions/will_focus.jpg',       
]

CARDS['advanced_actions'] = [
    'mk/cards/advanced_actions/agility.jpg',
    'mk/cards/advanced_actions/ambush.jpg',
    'mk/cards/advanced_actions/blood_rage.jpg',
    'mk/cards/advanced_actions/blood_ritual.jpg',
    'mk/cards/advanced_actions/crushing_blot.jpg',
    'mk/cards/advanced_actions/crystal_mastery.jpg',
    'mk/cards/advanced_actions/decompose.jpg',
    'mk/cards/advanced_actions/diplomacy.jpg',
    'mk/cards/advanced_actions/fire_bolt.jpg',
    'mk/cards/advanced_actions/frost_bridge.jpg',
    'mk/cards/advanced_actions/heroic_tale.jpg',
    'mk/cards/advanced_actions/ice_bolt.jpg',
    'mk/cards/advanced_actions/ice_shield.jpg',
    'mk/cards/advanced_actions/in_need.jpg',
    'mk/cards/advanced_actions/intimidate.jpg',
    'mk/cards/advanced_actions/into_the_heat.jpg',
    'mk/cards/advanced_actions/learning.jpg',
    'mk/cards/advanced_actions/magic_talent.jpg',
    'mk/cards/advanced_actions/mana_storm.jpg',
    'mk/cards/advanced_actions/maximal_effect.jpg',
    'mk/cards/advanced_actions/path_finding.jpg',
    'mk/cards/advanced_actions/pure_magic.jpg',
    'mk/cards/advanced_actions/refreshing_walk.jpg',
    'mk/cards/advanced_actions/regeneration.jpg',
    'mk/cards/advanced_actions/song_of_wind.jpg',
    'mk/cards/advanced_actions/steady_tempo.jpg',
    'mk/cards/advanced_actions/swift_bolt.jpg',
    'mk/cards/advanced_actions/training.jpg',
]

CARDS['spells'] = [
    'mk/cards/spells/burning_shield.jpg',
    'mk/cards/spells/call_to_arms.jpg',
    'mk/cards/spells/chill.jpg',
    'mk/cards/spells/demolish.jpg',
    'mk/cards/spells/energy_flow.jpg',
    'mk/cards/spells/expose.jpg',
    'mk/cards/spells/fireball.jpg',
    'mk/cards/spells/flame_wall.jpg',
    'mk/cards/spells/mana_bolt.jpg',
    'mk/cards/spells/mana_claim.jpg',
    'mk/cards/spells/mana_meltdown.jpg',
    'mk/cards/spells/meditation.jpg',
    'mk/cards/spells/mind_read.jpg',
    'mk/cards/spells/restoration.jpg',
    'mk/cards/spells/snowstorm.jpg',
    'mk/cards/spells/space_bending.jpg',
    'mk/cards/spells/tremor.jpg',
    'mk/cards/spells/underground_travel.jpg',
    'mk/cards/spells/whirlwind.jpg',
    'mk/cards/spells/wings_of_wind.jpg',
]

CARDS['artifacts'] = [
    'mk/cards/artifacts/amulet_of_darkness.jpg',
    'mk/cards/artifacts/amulet_of_sun.jpg',
    'mk/cards/artifacts/banner_of_courage.jpg',
    'mk/cards/artifacts/banner_of_fear.jpg',
    'mk/cards/artifacts/banner_of_glory.jpg',
    'mk/cards/artifacts/banner_of_protection.jpg',
    'mk/cards/artifacts/book_of_wisdom.jpg',
    'mk/cards/artifacts/diamond_ring.jpg',
    'mk/cards/artifacts/emerald_ring.jpg',
    'mk/cards/artifacts/endless_bag_of_gold.jpg',
    'mk/cards/artifacts/endless_gem_pouch.jpg',
    'mk/cards/artifacts/golden_grail.jpg',
    'mk/cards/artifacts/horn_of_wrath.jpg',
    'mk/cards/artifacts/ruby_ring.jpg',
    'mk/cards/artifacts/sapphire_ring.jpg',
    'mk/cards/artifacts/sword_of_justice.jpg',          
]

CARDS['regular_units'] = [
    'mk/cards/regular_units/foresters.jpg',
    'mk/cards/regular_units/guardian_golems.jpg',
    'mk/cards/regular_units/herbalists.jpg',
    'mk/cards/regular_units/illusionists.jpg',
    'mk/cards/regular_units/northern_monks.jpg',
    'mk/cards/regular_units/peasants.jpg',
    'mk/cards/regular_units/red_cape_monks.jpg',
    'mk/cards/regular_units/savage_monks.jpg',
    'mk/cards/regular_units/utem_crossbowmen.jpg',
    'mk/cards/regular_units/utem_guardsmen.jpg',
    'mk/cards/regular_units/utem_swordsmen.jpg',
     
]

CARDS['elite_units'] = [
    'mk/cards/elite_units/altem_guardians.jpg',
    'mk/cards/elite_units/altem_mages.jpg',
    'mk/cards/elite_units/amotep_freezers.jpg',
    'mk/cards/elite_units/amotep_gunners.jpg',
    'mk/cards/elite_units/catapults.jpg',
    'mk/cards/elite_units/fire_golems.jpg',
    'mk/cards/elite_units/fire_mages.jpg',
    'mk/cards/elite_units/ice_golems.jpg',
    'mk/cards/elite_units/ice_mages.jpg',
]

class CardsView(QtWidgets.QDialog):
    """This widget contains all cards of the game, distributed over several tabs. It is solely a reference
    for the player."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Cards")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        tabWidget = QtWidgets.QTabWidget()
        layout.addWidget(tabWidget)
        
        tabWidget.addTab(CardWidget('sites'), self.tr("Sites"))
        tabWidget.addTab(CardWidget('skills'), self.tr("Skills"))
        tabWidget.addTab(CardWidget('cities'), self.tr("Cities"))
        tabWidget.addTab(CardWidget('tactics_day'), self.tr("Day tactics"))
        tabWidget.addTab(CardWidget('tactics_night'), self.tr("Night tactics"))
        tabWidget.addTab(CardWidget('basic_actions'), self.tr("Basic actions"))
        tabWidget.addTab(CardWidget('advanced_actions'), self.tr("Advanced actions"))
        tabWidget.addTab(CardWidget('spells'), self.tr("Spells"))
        tabWidget.addTab(CardWidget('artifacts'), self.tr("Artifacts"))
        tabWidget.addTab(CardWidget('regular_units'), self.tr("Regular units"))
        tabWidget.addTab(CardWidget('elite_units'), self.tr("Elite units"))
        
        
class CardWidget(QtWidgets.QWidget):
    """Show cards of one category. Only one card is visible at the time. The widget offers buttons to
    go to the next and previous card."""
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.index = 0
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.label = QtWidgets.QLabel()
        self.label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        layout.addWidget(self.label, 1)
        
        buttonLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(buttonLayout)
        
        buttonLayout.addStretch(1)
        leftButton = QtWidgets.QToolButton()
        leftButton.setIcon(QtGui.QIcon.fromTheme("go-previous"))
        leftButton.clicked.connect(self.previous)
        buttonLayout.addWidget(leftButton)        
        
        self.indexLabel = QtWidgets.QLabel()
        buttonLayout.addWidget(self.indexLabel)
        
        rightButton = QtWidgets.QToolButton()
        rightButton.setIcon(QtGui.QIcon.fromTheme("go-next"))
        rightButton.clicked.connect(self.next)
        buttonLayout.addWidget(rightButton)
        buttonLayout.addStretch(1)
        
        # initialize
        if len(CARDS[self.category]) > 0:
            self.setIndex(0)
        else:
            leftButton.setEnabled(False)
            rightButton.setEnabled(False)
        
    def setIndex(self, index):
        """Set the number of the current card."""
        self.index = index % len(CARDS[self.category])
        self.label.setPixmap(utils.getPixmap(CARDS[self.category][self.index]))
        self.indexLabel.setText(self.tr("{} / {}").format(self.index+1, len(CARDS[self.category])))

    def previous(self):
        """Go to the previous card."""
        self.setIndex(self.index - 1)
        
    def next(self):
        """Go to the next card."""
        self.setIndex(self.index + 1)
