bl_info = {
    "name": "Shifter",
    "author": "Jacob Morris",
    "version": (0, 1),
    "blender": (2, 78, 0),
    "location": "View 3D > Toolbar > Shifter",
    "description": "Allows cuboidal objects to be resized easily without needing to enter editmode",
    "category": "Mesh"
    }

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

import bpy
from bpy.props import FloatVectorProperty, StringProperty, EnumProperty, FloatProperty
import bmesh


def update_shift(self, context):
    ob = context.object
    adjusted = False

    if context.mode != "EDIT_MESH":
        adjusted = True
        bpy.ops.object.editmode_toggle()

    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    verts = bm.verts

    new_shift = ob.shifter_shift
    old_shift = ob.shifter_last_shift
    x_indices = convert_from_string(ob.shifter_x_verts)
    y_indices = convert_from_string(ob.shifter_y_verts)
    z_indices = convert_from_string(ob.shifter_z_verts)

    for i in x_indices:
        verts[i].co = shift_position(verts[i].co, 0, new_shift[0], old_shift[0])

    for i in y_indices:
        verts[i].co = shift_position(verts[i].co, 1, new_shift[1], old_shift[1])

    for i in z_indices:
        verts[i].co = shift_position(verts[i].co, 2, new_shift[2], old_shift[2])

    ob.shifter_last_shift = ob.shifter_shift
    bmesh.update_edit_mesh(ob.data)

    if adjusted:
        bpy.ops.object.editmode_toggle()


def shift_position(vector, i, new_shift, old_shift):
    cur = vector[i] - old_shift + new_shift
    vector[i] = cur

    return vector


def convert_from_string(s: str) -> set:
    if s:
        sp = s.split(",")
        out = set({})
        for i in sp:
            out.add(int(i))

        return out
    else:
        return set([])


def convert_to_string(l: list) -> str:
    return ','.join(l)

bpy.types.Object.shifter_x_verts = StringProperty()
bpy.types.Object.shifter_y_verts = StringProperty()
bpy.types.Object.shifter_z_verts = StringProperty()
bpy.types.Object.shifter_last_shift = FloatVectorProperty(unit="LENGTH", default=(0, 0, 0))
bpy.types.Object.shifter_shift = FloatVectorProperty(name="Shift", unit="LENGTH", default=(0, 0, 0),
                                                     update=update_shift)


class ShifterPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_shifter_panel"
    bl_label = "Shifter Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        ob = context.object

        if ob is not None:
            if context.mode == "EDIT_MESH":
                for i in ["x", "y", "z"]:
                    verts_size = len(convert_from_string(eval("ob.shifter_{}_verts".format(i))))
                    layout.label("{} Vertices - Currently {}".format(i.capitalize(), verts_size))
                    row = layout.row()
                    row.operator("mesh.shifter_add", icon="ZOOMOUT").direction = i
                    row.operator("mesh.shifter_update", icon="FILE_REFRESH").direction = i
                    row.operator("mesh.shifter_clear", icon="CANCEL").direction = i
            else:
                layout.label("Enter Edit Mode To Adjust Vertices", icon="INFO")

            layout.separator()
            layout.prop(ob, "shifter_shift")

        else:
            layout.label("Please Select Object", icon="ERROR")


class ShifterClear(bpy.types.Operator):
    bl_idname = "mesh.shifter_clear"
    bl_label = "Clear"
    direction = StringProperty()

    @classmethod
    def poll(cls, context):
        return context.mode != "EDIT_MODE"

    def execute(self, context):
        ob = context.object

        if self.direction and ob is not None:
            if self.direction == "x":
                ob.shifter_x_verts = ""
            elif self.direction == "y":
                ob.shifter_y_verts = ""
            else:
                ob.shifter_z_verts = ""

        self.report({"INFO"}, "Shifter: Clear Vertices")
        return {"FINISHED"}


class ShifterAdd(bpy.types.Operator):
    bl_idname = "mesh.shifter_add"
    bl_label = "Add"
    direction = StringProperty()

    @classmethod
    def poll(cls, context):
        return context.mode != "EDIT_MODE"

    def execute(self, context):
        ob = context.object
        start_size = 0
        end_size = 0

        if self.direction and ob is not None:
            verts = bmesh.from_edit_mesh(ob.data).verts

            cur_set = convert_from_string(eval("ob.shifter_{}_verts".format(self.direction)))
            start_size = len(cur_set)

            for v in verts:
                if v.select and v.index not in cur_set:
                    cur_set.add(v.index)

            end_size = len(cur_set)
            str_list = [str(i) for i in cur_set]
            exec("ob.shifter_{}_verts = convert_to_string(str_list)".format(self.direction))

        self.report({"INFO"}, "Shifter: Added {} Vertices".format(end_size - start_size))
        return {"FINISHED"}


class ShifterUpdate(bpy.types.Operator):
    bl_idname = "mesh.shifter_update"
    bl_label = "Update"
    direction = StringProperty()

    @classmethod
    def poll(cls, context):
        return context.mode != "EDIT_MODE"

    def execute(self, context):
        ob = context.object
        size = 0

        if self.direction and ob is not None:
            verts = bmesh.from_edit_mesh(ob.data).verts
            str_list = []
            for v in verts:
                if v.select:
                    str_list.append(str(v.index))
            size = len(str_list)

            if self.direction == "x":
                ob.shifter_x_verts = convert_to_string(str_list)
            elif self.direction == "y":
                ob.shifter_y_verts = convert_to_string(str_list)
            else:
                ob.shifter_z_verts = convert_to_string(str_list)

        self.report({"INFO"}, "Shifter: Set {} Vertices".format(size))
        return {"FINISHED"}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
