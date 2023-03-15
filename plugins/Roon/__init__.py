# -*- coding: utf-8 -*-
#
# plugins/CambridgeAudioSerial/__init__.py
#
# This file is a plugin for EventGhost.
# Copyright © 2005-2018 EventGhost Project <http://www.eventghost.net/>
#
# EventGhost is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with EventGhost. If not, see <http://www.gnu.org/licenses/>.
#

help = '''\
Roon plugin
'''


eg.RegisterPlugin(
    name = 'Roon',
    author = 'Sonnabend',
    version = '0.1',
    kind = 'external',
    guid = "{d22e3226-580c-4a16-9415-b074026823c8}",
    description = 'Roon Control',
    url = "",
    help = help,
    canMultiLoad = False,
    createMacrosOnAdd = False,
)


import threading
import time
import re
import roonapi
import eg
import wx
import sys


class conf:
    FirstVolumeRepeatPause = 0.3
    NextVolumeRepeatPause = 0.110


class current:
    Volume = 50
    Mute = False


cmdList = (
('Power', None, None, None),
('PowerOn', 'Power On', '1,11,1', None),
('PowerOff', 'Power Standby', '1,11,0', None),
('Volume', None, None, None),
('MuteOff', 'Mute Off', '1,12,0', None),
('MuteOn', 'Mute On', '1,12,1', None),
('VolumeGoto', 'Goto Volume x (00-96, 96=0dB)', '1,13,x', '00-96'),
('VolumeUp', 'Volume Up', '1,14,', None),
('VolumeDown', 'Volume Down', '1,15,', None),
('VolumeStop', 'Volume Stop', '1,16,', None),
('BalanceSet', 'Set Balance Level x (00-16, 00:max left, 08:neutral, 16:max right)', '1,17,x', '00-16'),
('BalanceRight', 'Balance Right', '1,18,', None),
('BalanceLeft', 'Balance Left', '1,19,', None),
('SoftwareVersionGet', 'Get Software Version', '2,01,', None),
('ProtocolVersionGet', 'Get Protocol Version', '2,02,', None),

(None,None,None,None),
)

EventList = {
    '3':{
        'content':'Setup',
        '01':'SoftwareVersion',
        '02':'ProtocolVersion',
        '03':'InputNameChanged'
    },
    '4':{
        'content':'Update',
        '01':'Input1Selected',
        '02':'Input2Selected',
        '03':'Input3Selected',
        '04':'Input4Selected',
        '05':'Input5Selected',
        '06':'Input6Selected',
        '07':'Input7Selected',
        '08':'TapeMonitorChanged',
        '11':'PowerStateChanged',
        '12':'MuteStateChanged',
        '13':'VolumeChanged',
        '14':'Volume+',
        '15':'Volume-',
        '16':'VolumeStopped',
        '17':'BalanceChanged',
        '20':'LCDBrightnessChanged',
        '21':'SpeakerSelectionChanged',
        '22':'HeadphonesInOut',
        '23':'A-BUSInputSourceChanged',
        '24':'BassLevelChanged',
        '25':'TrebleLevelChanged',
        '26':'DirectStateChanged'
    },
    '5':{
        'content':'Error',
        '01':'Overload',
        '02':'DCOffset',
        '03':'OverTemperature',
        '04':'Clipping',
        '05':'MainsFail',
        '06':'SpeakerFail',
        '07':'CommandGroupUnknown',
        '08':'CommandNumberUnknown',
        '09':'CommandData'
    }
}



class CmdAction(eg.ActionClass):
    '''Base class for all argumentless actions'''

    def __call__(self):
        pass



class ValueAction(eg.ActionWithStringParameter):
    '''Base class for all actions with adjustable argument'''

    def __call__(self, data):
        pass



class Raw(eg.ActionWithStringParameter):
    name = 'Send Raw command'

    def __call__(self, data):
        pass



class VolumeAction(eg.ActionClass):
    def __call__(self):
        pass



class ToggleMuteAction(eg.ActionClass):
    def __call__(self):
        pass



class Roon(eg.PluginClass):

    def __init__(self):
        group = self
        for cmd_name, cmd_text, cmd_cmd, cmd_rangespec in cmdList:
            if cmd_text is None:
                # New subgroup, or back up
                if cmd_name is None:
                    group = self
                else:
                    group = self.AddGroup(cmd_name)
                if cmd_name == 'Volume': groupVolume = group
            elif cmd_rangespec is not None:
                # Command with argument
                actionName, paramDescr = cmd_text.split('(')
                actionName = actionName.strip()
                paramDescr = paramDescr[:-1]
                _cmdLeft, _cmdRight = cmd_cmd.split('x')

                class Action(ValueAction):
                    name = actionName
                    cmd = cmd_cmd
                    parameterDescription = 'Value: (%s)' % paramDescr
                    cmdLeft = _cmdLeft
                    cmdRight = _cmdRight
                Action.__name__ = cmd_name
                group.AddAction(Action)
            else:
                # Argumentless command
                class Action(CmdAction):
                    name = cmd_text
                    cmd = cmd_cmd
                Action.__name__ = cmd_name
                group.AddAction(Action)

        group.AddAction(Raw)

        class Action(VolumeAction):
            name = 'Volume Up until event end'
            increment = 1
        Action.__name__ = 'VolumeUpUntilEnd'
        groupVolume.AddAction(Action)

        class Action(VolumeAction):
            name = 'Volume Down until event end'
            increment = -1
        Action.__name__ = 'VolumeDownUntilEnd'
        groupVolume.AddAction(Action)

        class Action(ToggleMuteAction):
            name = 'Toggle Mute'
        Action.__name__ = 'ToggleMute'
        groupVolume.AddAction(Action)



    def __start__(self):
        pass


    def __stop__(self):
        pass

    def authorize(self, event):
        print('in {} with event {}'.format(sys._getframe().f_code.co_name,event))
        pass


    def Configure(self, port=0):
        panel = eg.ConfigPanel()
        infoGroupSizer = wx.StaticBoxSizer(
            wx.StaticBox(panel, -1, 'text.uuInfo'),
            wx.VERTICAL
        )
        infoSizer = wx.FlexGridSizer(3, 2)
        infoSizer.AddMany([
            (panel.StaticText('text.uuProtocol'), 0, wx.EXPAND),
            (panel.StaticText('protocolVersion'), 0, wx.EXPAND),
            (panel.StaticText('text.uuFirmVersion'), 0, wx.EXPAND),
            (panel.StaticText('firmwareVersion'), 0, wx.EXPAND),
            (panel.StaticText('text.uuFirmDate'), 0, wx.EXPAND),
            (panel.StaticText('firmwareDate'), 0, wx.EXPAND),
        ])
        infoGroupSizer.Add(infoSizer, 0, wx.LEFT, 5)
        panel.sizer.Add(infoGroupSizer, 0, wx.EXPAND)

        panel.sizer.Add((15, 15))

        ledGroupSizer = wx.StaticBoxSizer(
            wx.StaticBox(panel, -1, 'text.redIndicator'),
            wx.VERTICAL
        )
        panel.sizer.Add(ledGroupSizer, 0, wx.EXPAND)

        panel.sizer.Add((15, 15))
        receiveGroupSizer = wx.StaticBoxSizer(
            wx.StaticBox(panel, -1, 'text.irReception'),
            wx.VERTICAL
        )
        panel.sizer.Add(receiveGroupSizer, 0, wx.EXPAND)

        authorizeButton = wx.Button(panel, wx.ID_CANCEL, 'Authorize Plugin')
        authorizeButton.Bind(wx.EVT_BUTTON, self.authorize)
        authorizeButton.Enable(True)
        # self.burstButton = burstButton
        panel.sizer.Add(authorizeButton, 0, wx.EXPAND|wx.ALIGN_RIGHT)


        while panel.Affirmed():
            panel.SetResult()