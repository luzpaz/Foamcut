# -*- coding: utf-8 -*-

__title__ = "Create Route"
__author__ = "Andrew Shkolik & Andrei Bezborodov"
__license__ = "LGPL 2.1"
__doc__ = "Create a route from selected pathes."
__usage__ = """Select multiple paths in order of cutting and activate tool."""

import FreeCAD
App=FreeCAD
import FreeCADGui
Gui=FreeCADGui
import utilities

class WireRoute:
    def __init__(self, obj, objects, config):        
        obj.addProperty("App::PropertyString",      "Type", "", "", 5).Type = "Route"  
        obj.addProperty("App::PropertyLength",      "FieldWidth","","",5)

        obj.addProperty("App::PropertyLinkList",    "Objects",      "Task",   "Source data").Objects = objects
        obj.addProperty("App::PropertyIntegerList", "Data",         "Task",   "Data")
        obj.addProperty("App::PropertyBoolList",    "DataDirection","Task",   "Data Direction")

        obj.setExpression(".FieldWidth", u"<<{}>>.FieldWidth".format(config))
        obj.addProperty("App::PropertyString",    "Error", "", "", 5) 

        obj.Proxy = self

        self.execute(obj)

    def onChanged(self, fp, prop):
        # FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")
        pass
    
    def execute(self, obj): 
        obj.Error = ""

        first       = obj.Objects[0]
        reversed    = None        # - Second segment is reversed
        START       = 0           # - Segment start point index
        END         = -1          # - Segment end point index
        route_data  = []
        route_data_dir  = []
        item_index  = 0

        # - Check is single element
        if len(obj.Objects) == 1:
            # - Store element            
            route_data.append(item_index)
            route_data_dir.append(False)

        # - Walk through other objects
        for second in obj.Objects[1:]:
            item_index += 1

            # - Process skipped element
            if first is None:
                first = second
                if first.Type == "Enter":
                    route_data.append(item_index)
                    route_data_dir.append(False)

                print("SKIP: %s" % second.Type)
                continue
            
            if first.Type == "Projection" and first.PointsCount < 2:
                print("Vertex Projection - skip")
                first = second
                continue

            # - Skip rotation object
            if first.Type == "Rotation":
                print("R1")
                # - Store first element
                route_data.append(item_index - 1)
                route_data_dir.append(False)

                # - Check is rotation is firts element
                if item_index == 1:
                    # - Do not skip next element
                    first = second
                    continue
                else:
                    # - Go to next object
                    first = None
                    continue
            elif second.Type == "Rotation":
                print("R1 - 2")
                # - Store element
                route_data.append(item_index)
                route_data_dir.append(False)

                # - Skip element
                first = None
                continue
            elif first.Type == "Exit" and second.Type == "Enter":
                print("EXIT -> ENTER")
                # - Store first item
                if len(route_data) == 0:
                    # - Store element
                    route_data.append(item_index - 1)
                    route_data_dir.append(False)

                # - Store element
                route_data.append(item_index)
                route_data_dir.append(False)

                first = second
                continue
            
            # - Get lines on left plane
            if first.Type   == "Path" or first.Type == "Projection":    
                first_line  = first.Path_L
            elif first.Type == "Enter":   
                first_line  = [App.Vector(-obj.FieldWidth / 2, first.PointXL, first.PointZL)]
            elif first.Type == "Move":    
                first_line  = [
                    App.Vector(-obj.FieldWidth / 2, first.PointXL, first.PointZL),
                    App.Vector(-obj.FieldWidth / 2, first.PointXL + float(first.InXDirection), first.PointZL + float(first.InZDirection))
                ]
            elif first.Type == "Join":    
                first_line  = [
                    App.Vector(-obj.FieldWidth / 2, first.PointXLA, first.PointZLA),
                    App.Vector(-obj.FieldWidth / 2, first.PointXLB, first.PointZLB)
                ]
            else:
                obj.Error = "ERROR: {} - Unsupported first element. Second = {}".format(first.Label, second.Label)
                print(obj.Error)                
                return False
            
            if second.Type == "Path" or second.Type == "Projection":   
                second_line = second.Path_L
            elif second.Type == "Exit": 
                second_line = [App.Vector(-obj.FieldWidth / 2, second.PointXL, second.PointZL)]
            elif second.Type == "Move": 
                second_line = [
                    App.Vector(-obj.FieldWidth / 2, second.PointXL, second.PointZL),
                    App.Vector(-obj.FieldWidth / 2, second.PointXL + float(second.InXDirection), second.PointZL + float(second.InZDirection))
                ]
            elif second.Type == "Join":    
                second_line  = [
                    App.Vector(-obj.FieldWidth / 2, second.PointXLA, second.PointZLA),
                    App.Vector(-obj.FieldWidth / 2, second.PointXLB, second.PointZLB)
                ]
            else:
                print("Unsupported second element")
                obj.Error = "ERROR: {} - Unsupported second element. First = {}".format(second.Label, first.Label)
                print(obj.Error) 
                return False
            
            if reversed is None:
                first_reversed = False

                # - Detect first pair
                if utilities.isCommonPoint(first_line[END], second_line[START]):
                    print ("First connected: FWD - FWD")
                    reversed = False
                elif utilities.isCommonPoint(first_line[END], second_line[END]):
                    print ("First connected: FWD - REV")
                    reversed = True
                elif utilities.isCommonPoint(first_line[START], second_line[START]):
                    print ("First connected: REV - FWD")
                    first_reversed  = True
                    reversed        = False
                elif utilities.isCommonPoint(first_line[START], second_line[END]):
                    print ("First connected: REV - REV")
                    first_reversed  = True
                    reversed        = True
                else:
                    obj.Error = "ERROR: {} not connected with {}".format(first.Label, second.Label)
                    print(obj.Error)
                    return False
                
                # - Store first element
                route_data.append(item_index - 1)
                route_data_dir.append(first_reversed)

                # - Store second element
                route_data.append(item_index)
                route_data_dir.append(reversed)
            else:
                # - Detect next pairs
                if utilities.isCommonPoint(first_line[START if reversed else END], second_line[START]):
                    print ("Connected: FWD - FWD")
                    reversed = False
                elif utilities.isCommonPoint(first_line[START if reversed else END], second_line[END]):
                    print ("Connected: FWD - REV")
                    reversed = True
                else:
                    obj.Error = "ERROR: {} not connected with {}".format(first.Label, second.Label)
                    print(obj.Error)
                    return False

                # - Store next element
                route_data.append(item_index)
                route_data_dir.append(reversed)

            # - Go to next object
            first = second
        
        if len(route_data) != len(route_data_dir) or len(route_data) == 0:
            obj.Error("Error: Data calculation error.")
            print(obj.Error)
            return False
        
        obj.Data = route_data
        obj.DataDirection = route_data_dir


class WireRouteVP:
    def __init__(self, obj):
        obj.Proxy = self

    def attach(self, obj):
        self.Object = obj.Object

    def getIcon(self):
        return utilities.getIconPath("route.svg")

    if utilities.isNewStateHandling(): # - currently supported only in main branch FreeCad v0.21.2 and up
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None
    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

        def __setstate__(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None
    
    def claimChildren(self):
        return [object for object in self.Object.Objects]
    
    def doubleClicked(self, obj):
        return True
    
    def onDelete(self, feature, subelements):
        group = Gui.ActiveDocument.ActiveView.getActiveObject("group")
        if group is not None and group.Type == "Job":
            for obj in self.Object.Objects:
                group.addObject(obj)
        return True

class MakeRoute():
    """Make Route"""

    def GetResources(self):
        return {"Pixmap"  : utilities.getIconPath("route.svg"), # the name of a svg file available in the resources
                'Accel' : "", # a default shortcut (optional)
                "MenuText": "Create a route",
                "ToolTip" : "Create a route from selected paths"}

    def Activated(self): 
        group = Gui.ActiveDocument.ActiveView.getActiveObject("group")
        if group is not None and group.Type == "Job":        
            # - Get selecttion
            objects = [item.Object for item in Gui.Selection.getSelectionEx()]
            
            for object in objects:
                object.touch()
            
            group.recompute()

            # - Create object
            route = group.newObject("App::FeaturePython", "Route")
            WireRoute(route, objects, group.ConfigName)
            WireRouteVP(route.ViewObject)

            for obj in objects:
                group.removeObject(obj)

            App.ActiveDocument.recompute()
            Gui.Selection.clearSelection()
    
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            group = Gui.ActiveDocument.ActiveView.getActiveObject("group")
            if group is not None and group.Type == "Job":
                # - Get selected objects
                objects = [item.Object for item in Gui.Selection.getSelectionEx()]

                # - nothing selected
                if len(objects) == 0:
                    return False
                
                for obj in objects:
                    if not hasattr(obj, "Type") or obj.Type not in utilities.FC_TYPES_TO_ROUTE:
                        return False                    
                return True
            return False
            
Gui.addCommand("Route", MakeRoute())
