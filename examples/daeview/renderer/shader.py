#
# Copyright Tristam Macdonald 2008.
#
# Distributed under the Boost Software License, Version 1.0
# (see http://www.boost.org/LICENSE_1_0.txt)
#

from pyglet.gl import *
import ctypes

class Shader:
	# vert, frag and geom take arrays of source strings
	# the arrays will be concattenated into one string by OpenGL
	def __init__(self, vert = [], frag = [], geom = []):
		# create the program handle
		self.handle = glCreateProgram()
		# we are not linked yet
		self.linked = False

		# create the vertex shader
		self.createShader(vert, GL_VERTEX_SHADER)
		# create the fragment shader
		self.createShader(frag, GL_FRAGMENT_SHADER)
		# the geometry shader will be the same, once pyglet supports the extension
		# self.createShader(frag, GL_GEOMETRY_SHADER_EXT)

		# attempt to link the program
		self.link()

	def createShader(self, strings, type):
		count = len(strings)
		# if we have no source code, ignore this shader
		if count < 1:
			return

		# create the shader handle
		shader = glCreateShader(type)

		# convert the source strings into a ctypes pointer-to-char array, and upload them
		# this is deep, dark, dangerous black magick - don't try stuff like this at home!
		src = (ctypes.c_char_p * count)(*strings)
		glShaderSource(shader, count, ctypes.cast(ctypes.pointer(src),
			       ctypes.POINTER(ctypes.POINTER(ctypes.c_char))), None)

		# compile the shader
		glCompileShader(shader)

		temp = ctypes.c_int(0)
		# retrieve the compile status
		glGetShaderiv(shader, GL_COMPILE_STATUS, ctypes.byref(temp))

		# if compilation failed, print the log
		if not temp:
			# retrieve the log length
			glGetShaderiv(shader, GL_INFO_LOG_LENGTH, ctypes.byref(temp))
			# create a buffer for the log
			buffer = ctypes.create_string_buffer(temp.value)
			# retrieve the log text
			glGetShaderInfoLog(shader, temp, None, buffer)
			# print the log to the console
			print buffer.value
		else:
			# all is well, so attach the shader to the program
			glAttachShader(self.handle, shader);

	def link(self):
		# link the program
		glLinkProgram(self.handle)

		temp = ctypes.c_int(0)
		# retrieve the link status
		glGetProgramiv(self.handle, GL_LINK_STATUS, ctypes.byref(temp))

		# if linking failed, print the log
		if not temp:
			#	retrieve the log length
			glGetProgramiv(self.handle, GL_INFO_LOG_LENGTH, ctypes.byref(temp))
			# create a buffer for the log
			buffer = create_string_buffer(temp.value)
			# retrieve the log text
			glGetProgramInfoLog(self.handle, temp, None, buffer)
			# print the log to the console
			print buffer.value
		else:
			# all is well, so we are linked
			self.linked = True

	def bind(self):
		# bind the program
		glUseProgram(self.handle)

	def unbind(self):
		# unbind whatever program is currently bound - not necessarily this program,
		# so this should probably be a class method instead
		glUseProgram(0)

	# upload a floating point uniform
	# this program must be currently bound
	def uniformf(self, name, *vals):
		# check there are 1-4 values
		if len(vals) in range(1, 5):
			# select the correct function
			{ 1 : glUniform1f,
				2 : glUniform2f,
				3 : glUniform3f,
				4 : glUniform4f
				# retrieve the uniform location, and set
			}[len(vals)](glGetUniformLocation(self.handle, name), *vals)

	# upload an integer uniform
	# this program must be currently bound
	def uniformi(self, name, *vals):
		# check there are 1-4 values
		if len(vals) in range(1, 5):
			# select the correct function
			{ 1 : glUniform1i,
				2 : glUniform2i,
				3 : glUniform3i,
				4 : glUniform4i
				# retrieve the uniform location, and set
			}[len(vals)](glGetUniformLocation(self.handle, name), *vals)

	# upload a uniform matrix
	# works with matrices stored as lists,
	# as well as euclid matrices
	def uniform_matrixf(self, name, mat):
		# obtian the uniform location
		loc = glGetUniformLocation(self.Handle, name)
		# uplaod the 4x4 floating point matrix
		glUniformMatrix4fv(loc, 1, False, (c_float * 16)(*mat))

