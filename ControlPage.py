# -*- coding: ascii -*-
# $Id$
#
# Author: vvlachoudis@gmail.com
# Date: 18-Jun-2015

from __future__ import absolute_import
from __future__ import print_function
__author__ = "Vasilis Vlachoudis"
__email__  = "vvlachoudis@gmail.com"

try:
	from Tkinter import *
	import tkMessageBox
except ImportError:
	from tkinter import *
	import tkinter.messagebox as tkMessageBox

import math

from CNC import CNC
import Utils
import Ribbon
import Sender
import tkExtra
import Unicode
import CNCRibbon
from Sender import ERROR_CODES
from CNC import WCS,WCS_TEXT, DISTANCE_MODE, FEED_MODE, UNITS, PLANE

_LOWSTEP   = 0.0001
_HIGHSTEP  = 1000.0
_HIGHZSTEP = 10.0
_NOZSTEP = 'XY'

OVERRIDES = ["Feed", "Rapid", "Spindle"]


#===============================================================================
# Connection Group
#===============================================================================
class ConnectionGroup(CNCRibbon.ButtonMenuGroup):
	def __init__(self, master, app):
		CNCRibbon.ButtonMenuGroup.__init__(self, master, N_("Connection"), app,
			[(_("Hard Reset"),  "reset",     app.hardReset) ])
		self.grid2rows()

		# ---
		col,row=0,0
		b = Ribbon.LabelButton(self.frame,
				image=Utils.icons["home32"],
				text=_("Home"),
				compound=TOP,
				anchor=W,
				command=app.home,
				background=Ribbon._BACKGROUND)
		b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=NSEW)
		tkExtra.Balloon.set(b, _("Perform a homing cycle [$H]"))
		self.addWidget(b)

		# ---
		col,row=1,0
		b = Ribbon.LabelButton(self.frame,
				image=Utils.icons["unlock"],
				text=_("Unlock"),
				compound=LEFT,
				anchor=W,
				command=app.unlock,
				background=Ribbon._BACKGROUND)
		b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
		tkExtra.Balloon.set(b, _("Unlock controller [$X]"))
		self.addWidget(b)

		row += 1
		b = Ribbon.LabelButton(self.frame,
				image=Utils.icons["serial"],
				text=_("Connection"),
				compound=LEFT,
				anchor=W,
				command=lambda s=self : s.event_generate("<<Connect>>"),
				background=Ribbon._BACKGROUND)
		b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
		tkExtra.Balloon.set(b, _("Open/Close connection"))
		self.addWidget(b)

		row += 1
		b = Ribbon.LabelButton(self.frame,
				image=Utils.icons["reset"],
				text=_("Reset"),
				compound=LEFT,
				anchor=W,
				command=app.softReset,
				background=Ribbon._BACKGROUND)
		b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
		tkExtra.Balloon.set(b, _("Software reset of controller [ctrl-x]"))
		self.addWidget(b)


#===============================================================================
# User Group
#===============================================================================
class UserGroup(CNCRibbon.ButtonGroup):
	def __init__(self, master, app):
		CNCRibbon.ButtonGroup.__init__(self, master, "User", app)
		self.grid3rows()

		n = Utils.getInt("Buttons","n",6)
		for i in range(1,n):
			b = Utils.UserButton(self.frame, self.app, i,
					anchor=W,
					background=Ribbon._BACKGROUND)
			col,row = divmod(i-1,3)
			b.grid(row=row, column=col, sticky=NSEW)
			self.addWidget(b)


#===============================================================================
# Run Group
#===============================================================================
class RunGroup(CNCRibbon.ButtonGroup):
	def __init__(self, master, app):
		CNCRibbon.ButtonGroup.__init__(self, master, "Run", app)

		b = Ribbon.LabelButton(self.frame, self, "<<Run>>",
				image=Utils.icons["start32"],
				text=_("Start"),
				compound=TOP,
				background=Ribbon._BACKGROUND)
		b.pack(side=LEFT, fill=BOTH)
		tkExtra.Balloon.set(b, _("Run g-code commands from editor to controller"))
		self.addWidget(b)

		b = Ribbon.LabelButton(self.frame, self, "<<Pause>>",
				image=Utils.icons["pause32"],
				text=_("Pause"),
				compound=TOP,
				background=Ribbon._BACKGROUND)
		b.pack(side=LEFT, fill=BOTH)
		tkExtra.Balloon.set(b, _("Pause running program. Sends either FEED_HOLD ! or CYCLE_START ~"))

		b = Ribbon.LabelButton(self.frame, self, "<<Stop>>",
				image=Utils.icons["stop32"],
				text=_("Stop"),
				compound=TOP,
				background=Ribbon._BACKGROUND)
		b.pack(side=LEFT, fill=BOTH)
		tkExtra.Balloon.set(b, _("Pause running program and soft reset controller to empty the buffer."))



#===============================================================================
# ControlFrame
#===============================================================================
class ControlFrame(CNCRibbon.PageExLabelFrame):
	def __init__(self, master, app):
		CNCRibbon.PageExLabelFrame.__init__(self, master, "Control", _("Control"), app)

		frame = Frame(self())
		frame.pack(side=TOP, fill=X)

		row,col = 0,0
		Label(frame, text=_("Z")).grid(row=row, column=col)

		col += 3
		Label(frame, text=_("Y")).grid(row=row, column=col)

		# ---
		row += 1
		col = 0

		width=3
		height=2

		b = Button(frame, text=Unicode.BLACK_UP_POINTING_TRIANGLE,
					command=self.moveZup,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move +Z"))
		self.addWidget(b)

		col += 2
		b = Button(frame, text=Unicode.UPPER_LEFT_TRIANGLE,
					command=self.moveXdownYup,
					width=width, height=height,
					activebackground="LightYellow")

		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move -X +Y"))
		self.addWidget(b)

		col += 1
		b = Button(frame, text=Unicode.BLACK_UP_POINTING_TRIANGLE,
					command=self.moveYup,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move +Y"))
		self.addWidget(b)

		col += 1
		b = Button(frame, text=Unicode.UPPER_RIGHT_TRIANGLE,
					command=self.moveXupYup,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move +X +Y"))
		self.addWidget(b)

		col += 2
		b = Button(frame, text=u"\u00D710",
				command=self.mulStep,
				width=3,
				padx=1, pady=1)
		b.grid(row=row, column=col, sticky=EW+S)
		tkExtra.Balloon.set(b, _("Multiply step by 10"))
		self.addWidget(b)

		col += 1
		b = Button(frame, text=_("+"),
				command=self.incStep,
				width=3,
				padx=1, pady=1)
		b.grid(row=row, column=col, sticky=EW+S)
		tkExtra.Balloon.set(b, _("Increase step by 1 unit"))
		self.addWidget(b)

		# ---
		row += 1

		col = 1
		Label(frame, text=_("X"), width=3, anchor=E).grid(row=row, column=col, sticky=E)

		col += 1
		b = Button(frame, text=Unicode.BLACK_LEFT_POINTING_TRIANGLE,
					command=self.moveXdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move -X"))
		self.addWidget(b)

		col += 1
		b = Utils.UserButton(frame, self.app, 0, text=Unicode.LARGE_CIRCLE,
					command=self.go2origin,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move to Origin.\nUser configurable button.\nRight click to configure."))
		self.addWidget(b)

		col += 1
		b = Button(frame, text=Unicode.BLACK_RIGHT_POINTING_TRIANGLE,
					command=self.moveXup,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move +X"))
		self.addWidget(b)

		# --
		col += 1
		Label(frame,"",width=2).grid(row=row,column=col)

		col += 1
		self.step = tkExtra.Combobox(frame, width=6, background="White")
		self.step.grid(row=row, column=col, columnspan=2, sticky=EW)
		self.step.set(Utils.config.get("Control","step"))
		self.step.fill(map(float, Utils.config.get("Control","steplist").split()))
		tkExtra.Balloon.set(self.step, _("Step for every move operation"))
		self.addWidget(self.step)

		# -- Separate zstep --
		try:
			zstep = Utils.config.get("Control","zstep")
			self.zstep = tkExtra.Combobox(frame, width=4, background="White")
			self.zstep.grid(row=row, column=0, columnspan=1, sticky=EW)
			self.zstep.set(zstep)
			zsl = [_NOZSTEP]
			zsl.extend(map(float, Utils.config.get("Control","zsteplist").split()))
			self.zstep.fill(zsl)
			tkExtra.Balloon.set(self.zstep, _("Step for Z move operation"))
			self.addWidget(self.zstep)
		except:
			self.zstep = self.step

		# Default steppings
		try:
			self.step1 = Utils.getFloat("Control","step1")
		except:
			self.step1 = 0.1

		try:
			self.step2 = Utils.getFloat("Control","step2")
		except:
			self.step2 = 1

		try:
			self.step3 = Utils.getFloat("Control","step3")
		except:
			self.step3 = 10

		# ---
		row += 1
		col = 0

		b = Button(frame, text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
					command=self.moveZdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move -Z"))
		self.addWidget(b)

		col += 2
		b = Button(frame, text=Unicode.LOWER_LEFT_TRIANGLE,
					command=self.moveXdownYdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move -X -Y"))
		self.addWidget(b)

		col += 1
		b = Button(frame, text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
					command=self.moveYdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move -Y"))
		self.addWidget(b)

		col += 1
		b = Button(frame, text=Unicode.LOWER_RIGHT_TRIANGLE,
					command=self.moveXupYdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=EW)
		tkExtra.Balloon.set(b, _("Move +X -Y"))
		self.addWidget(b)

		col += 2
		b = Button(frame, text=u"\u00F710",
					command=self.divStep,
					padx=1, pady=1)
		b.grid(row=row, column=col, sticky=EW+N)
		tkExtra.Balloon.set(b, _("Divide step by 10"))
		self.addWidget(b)

		col += 1
		b = Button(frame, text=_("-"),
					command=self.decStep,
					padx=1, pady=1)
		b.grid(row=row, column=col, sticky=EW+N)
		tkExtra.Balloon.set(b, _("Decrease step by 1 unit"))
		self.addWidget(b)

		#self.grid_columnconfigure(6,weight=1)
		try:
	#			self.grid_anchor(CENTER)
			self.tk.call("grid","anchor",self,CENTER)
		except TclError:
			pass

	#----------------------------------------------------------------------
	def saveConfig(self):
		Utils.setFloat("Control", "step", self.step.get())
		if self.zstep is not self.step:
			Utils.setFloat("Control", "zstep", self.zstep.get())

	#----------------------------------------------------------------------
	# Jogging
	#----------------------------------------------------------------------
	def getStep(self, axis='x'):
		if axis == 'z':
			zs = self.zstep.get()
			if zs == _NOZSTEP:
				return self.step.get()
			else:
				return zs
		else:
			return self.step.get()

	def moveXup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("X%s"%(self.step.get()))

	def moveXdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("X-%s"%(self.step.get()))

	def moveYup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("Y%s"%(self.step.get()))

	def moveYdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("Y-%s"%(self.step.get()))

	def moveXdownYup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("X-%sY%s"%(self.step.get(),self.step.get()))

	def moveXupYup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("X%sY%s"%(self.step.get(),self.step.get()))

	def moveXdownYdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("X-%sY-%s"%(self.step.get(),self.step.get()))

	def moveXupYdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("X%sY-%s"%(self.step.get(),self.step.get()))

	def moveZup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("Z%s"%(self.getStep('z')))

	def moveZdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.app.mcontrol.jog("Z-%s"%(self.getStep('z')))

	def go2origin(self, event=None):
		self.sendGCode("G90")
		self.sendGCode("G0Z%d"%(CNC.vars['safe']))
		self.sendGCode("G0X0Y0")
		self.sendGCode("G0Z0")

	#----------------------------------------------------------------------
	def setStep(self, s, zs=None):
		self.step.set("%.4g"%(s))
		if self.zstep is self.step or zs is None:
			self.event_generate("<<Status>>",
				data=_("Step: %g")%(s))
				#data=(_("Step: %g")%(s)).encode("utf8"))
		else:
			self.zstep.set("%.4g"%(zs))
			self.event_generate("<<Status>>",
				data=_("Step: %g    Zstep:%g ")%(s,zs))
				#data=(_("Step: %g    Zstep:%g ")%(s,zs)).encode("utf8"))

	#----------------------------------------------------------------------
	@staticmethod
	def _stepPower(step):
		try:
			step = float(step)
			if step <= 0.0: step = 1.0
		except:
			step = 1.0
		power = math.pow(10.0,math.floor(math.log10(step)))
		return round(step/power)*power, power

	#----------------------------------------------------------------------
	def incStep(self, event=None):
		if event is not None and not self.acceptKey(): return
		step, power = ControlFrame._stepPower(self.step.get())
		s = step+power
		if s<_LOWSTEP: s = _LOWSTEP
		elif s>_HIGHSTEP: s = _HIGHSTEP
		if self.zstep is not self.step and self.zstep.get() != _NOZSTEP:
			step, power = ControlFrame._stepPower(self.zstep.get())
			zs = step+power
			if zs<_LOWSTEP: zs = _LOWSTEP
			elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
		else:
			zs=None
		self.setStep(s, zs)

	#----------------------------------------------------------------------
	def decStep(self, event=None):
		if event is not None and not self.acceptKey(): return
		step, power = ControlFrame._stepPower(self.step.get())
		s = step-power
		if s<=0.0: s = step-power/10.0
		if s<_LOWSTEP: s = _LOWSTEP
		elif s>_HIGHSTEP: s = _HIGHSTEP
		if self.zstep is not self.step and self.zstep.get() != _NOZSTEP:
			step, power = ControlFrame._stepPower(self.zstep.get())
			zs = step-power
			if zs<=0.0: zs = step-power/10.0
			if zs<_LOWSTEP: zs = _LOWSTEP
			elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
		else:
			zs=None
		self.setStep(s, zs)

	#----------------------------------------------------------------------
	def mulStep(self, event=None):
		if event is not None and not self.acceptKey(): return
		step, power = ControlFrame._stepPower(self.step.get())
		s = step*10.0
		if s<_LOWSTEP: s = _LOWSTEP
		elif s>_HIGHSTEP: s = _HIGHSTEP
		if self.zstep is not self.step and self.zstep.get() != _NOZSTEP:
			step, power = ControlFrame._stepPower(self.zstep.get())
			zs = step*10.0
			if zs<_LOWSTEP: zs = _LOWSTEP
			elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
		else:
			zs=None
		self.setStep(s, zs)

	#----------------------------------------------------------------------
	def divStep(self, event=None):
		if event is not None and not self.acceptKey(): return
		step, power = ControlFrame._stepPower(self.step.get())
		s = step/10.0
		if s<_LOWSTEP: s = _LOWSTEP
		elif s>_HIGHSTEP: s = _HIGHSTEP
		if self.zstep is not self.step and self.zstep.get() != _NOZSTEP:
			step, power = ControlFrame._stepPower(self.zstep.get())
			zs = step/10.0
			if zs<_LOWSTEP: zs = _LOWSTEP
			elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
		else:
			zs=None
		self.setStep(s, zs)

	#----------------------------------------------------------------------
	def setStep1(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.setStep(self.step1, self.step1)

	#----------------------------------------------------------------------
	def setStep2(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.setStep(self.step2, self.step2)

	#----------------------------------------------------------------------
	def setStep3(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.setStep(self.step3, self.step2)


#===============================================================================
# Control Page
#===============================================================================
class ControlPage(CNCRibbon.Page):
	__doc__ = _("CNC communication and control")
	_name_  = N_("Control")
	_icon_  = "control"

	#----------------------------------------------------------------------
	# Add a widget in the widgets list to enable disable during the run
	#----------------------------------------------------------------------
	def register(self):
		global wcsvar
		wcsvar = IntVar()
		wcsvar.set(0)

		self._register((ConnectionGroup, UserGroup, RunGroup),
			(ControlFrame,))
