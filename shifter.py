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
from mathutils import Vector


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
    x_indices = from_string(ob.shifter_x_verts)
    y_indices = from_string(ob.shifter_y_verts)
    z_indices = from_string(ob.shifter_z_verts)

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


def shift_position(vector: Vector, i: int, new_shift: float, old_shift: float) -> Vector:
    cur = vector[i] - old_shift + new_shift
    vector[i] = cur

    return vector


def from_string(s: str) -> set:
    if s:
        sp = s.split(",")
        out = set({})
        for i in sp:
            out.add(int(i))

        return out
    else:
        return set([])


def to_string(l: list) -> str:
    l2 = [str(i) for i in l]
    return ','.join(l2)


bpy.types.Object.shifter_x_verts = StringProperty()
bpy.types.Object.shifter_y_verts = StringProperty()
bpy.types.Object.shifter_z_verts = StringProperty()
bpy.types.Object.shifter_last_shift = FloatVectorProperty(unit="LENGTH", default=(0, 0, 0))
bpy.types.Object.shifter_shift = FloatVectorProperty(name="Shift", unit="LENGTH", default=(0, 0, 0),
                                                     update=update_shift)


class ShifterPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_shifter_panel"
    bl_label = "Shifter"
    bl_category = "Shifter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        ob = context.object

        if ob is not None:
            vals = {"x": from_string(ob.shifter_x_verts), "y": from_string(ob.shifter_y_verts),
                    "z": from_string(ob.shifter_z_verts)}

            if context.mode == "EDIT_MESH":
                for i in ["x", "y", "z"]:
                    layout.label("{} Vertices - Currently {}".format(i.capitalize(), len(vals[i])))
                    row = layout.row()
                    row.operator("mesh.shifter_add", icon="ZOOMIN").direction = i
                    row.operator("mesh.shifter_remove", icon="ZOOMOUT").direction = i
                    row.operator("mesh.shifter_update", icon="FILE_REFRESH").direction = i
                    row.operator("mesh.shifter_clear", icon="CANCEL").direction = i
            else:
                if not len(vals['x']) and not len(vals['y']) and not len(vals['z']):
                    layout.operator("mesh.shifter_convert", icon="OBJECT_DATA")
                else:
                    layout.label("Enter Edit Mode To Adjust Vertex Groups", icon="INFO")

            layout.separator()
            layout.prop(ob, "shifter_shift")

        else:
            layout.label("Please Select An Object", icon="ERROR")


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

        if self.direction and ob is not None:
            verts = bmesh.from_edit_mesh(ob.data).verts

            cur_set = from_string(eval("ob.shifter_{}_verts".format(self.direction)))
            start_size = len(cur_set)

            for v in verts:
                if v.select and v.index not in cur_set:
                    cur_set.add(v.index)

            end_size = len(cur_set)
            exec("ob.shifter_{}_verts = to_string(list(cur_set))".format(self.direction))

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

        if self.direction and ob is not None:
            verts = bmesh.from_edit_mesh(ob.data).verts
            indices = []
            for v in verts:
                if v.select:
                    indices.append(v.index)
            size = len(indices)

            if self.direction == "x":
                ob.shifter_x_verts = to_string(indices)
            elif self.direction == "y":
                ob.shifter_y_verts = to_string(indices)
            else:
                ob.shifter_z_verts = to_string(indices)

            self.report({"INFO"}, "Shifter: Set {} Vertices".format(size))

        return {"FINISHED"}


class ShifterRemove(bpy.types.Operator):
    bl_idname = "mesh.shifter_remove"
    bl_label = "Remove"
    direction = StringProperty()

    @classmethod
    def poll(cls, context):
        return context.mode != "EDIT_MODE"

    def execute(self, context):
        ob = context.object

        if self.direction and ob is not None:
            verts = bmesh.from_edit_mesh(ob.data).verts
            cur_verts = from_string(eval("ob.shifter_{}_verts".format(self.direction)))
            removed = 0

            for v in verts:
                if v.select and v.index in cur_verts:
                    cur_verts.remove(v.index)
                    removed += 1

            exec("ob.shifter_{}_verts = to_string(list(cur_verts))".format(self.direction))
            self.report({"INFO"}, "Shifter: Removed {} Vertices".format(removed))

        return {"FINISHED"}


class ShifterConvert(bpy.types.Operator):
    bl_idname = "mesh.shifter_convert"
    bl_label = "Convert"
    bl_description = 'Try to automatically determine vertices groups'

    @classmethod
    def poll(cls, context):
        return context.mode != "EDIT_MODE"

    def execute(self, context):
        ob = context.object

        if ob is not None:
            bpy.ops.object.editmode_toggle()
            verts = bmesh.from_edit_mesh(ob.data).verts
            center = Vector((0, 0, 0))
            size = 0

            for v in verts:
                center += v.co
            center /= len(verts)

            indices = [[], [], []]

            for v in verts:
                if v.co[0] > center[0]:
                    indices[0].append(v.index)
                    size += 1
                if v.co[1] > center[1]:
                    indices[1].append(v.index)
                    size += 1
                if v.co[2] > center[2]:
                    indices[2].append(v.index)
                    size += 1

            ob.shifter_x_verts = to_string(indices[0])
            ob.shifter_y_verts = to_string(indices[1])
            ob.shifter_z_verts = to_string(indices[2])
            bpy.ops.object.editmode_toggle()

            self.report({"INFO"}, "Shifter: Setup {} Vertices In X, Y, Z Groups".format(size))
        return {"FINISHED"}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
