#Author-Aleksandr Krivosheev
#Description-Sprocket Gear Creator for Russian GOST

import adsk.core, adsk.fusion, adsk.cam, traceback, math, os.path, csv

handlers = []

def run(context):
    try:

        # Объявлены переменные, доступные во всем проекте
        global app, ui, mpath, spath
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Переменная ­ путь к файлу параметров модели
        spath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Source\config.csv')

        # Создание переменной cmdDef для новой команды
        cmdDef = ui.commandDefinitions.itemById('Sprocket')
        if not cmdDef:
            # Задание окна команды с указанным названием
            cmdDef = ui.commandDefinitions.addButtonDefinition('Sprocket','Sprocket Gear Creator','')

        # Создание обработчика  события выполнения команды cmdDef
        onCommandCreated = sprocketHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)

        # Вызов команды на выполнение
        cmdDef.execute()

        # Задание ожидания действий пользователя до завершения модуля
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class sprocketHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Обращение к команде, связанной с обработчиком
            cmd = adsk.core.Command.cast(args.command) 
            # Обращение к коллекции элементов управления, связанных с командой
            inputs = cmd.commandInputs

            # Создание формы для указания вида цепи
            typeChain = inputs.addDropDownCommandInput('typeChain', 'Тип цепи по ГОСТ 13568-97', adsk.core.DropDownStyles.TextListDropDownStyle)

            # Чтение в переменную typeChain типа цепи из файла данных
            try:
                with open(spath, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        typeChain.listItems.add(row[0], False, ' ')
            except:
                # Инициализация переменной при ошибке чтения файла
                ui.messageBox('Ошибка чтения файла')

            # Создание формы для указания числа зубьев звездочки
            inputs.addValueInput('numTeeth', 'Число зубьев звездочки', '', adsk.core.ValueInput.createByReal(20))

            # Создание формы для указания диаметра отверстия
            inputs.addValueInput('holeDiam', 'Диаметр отверстия', '', adsk.core.ValueInput.createByReal(10))       

            # Создание обработчика нажатия кнопки OK в окне генератора
            onExecute = sprocketCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class sprocketCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:

            # Получение доступа к элементам управления окна генерации звездочки
            command = args.firingEvent.sender
            hole_diam = command.commandInputs.itemById('holeDiam').value
            num_teeth = command.commandInputs.itemById('numTeeth').value
            type_chain = command.commandInputs.itemById ('typeChain').selectedItem.name

            # Получение данных из csv файла
            try:
                with open(spath, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if str(row[0]) == type_chain:
                            step_chain = float(row[1]) 
                            width_chain = float(row[2])
                            val_diam = float(row[3])
                            roll_diam = float(row[4])
                            height_chain = float(row[5])
                        else:
                            continue  
            except:
                # Инициализация переменной при ошибке чтения файла
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

            # Геометрическая характеристика зацепления
            geometric_characteristic_engagement = step_chain/roll_diam

            # Диаметр делительной окружно­сти
            pitch_circle_diam = step_chain/(math.sin(math.radians(180)/num_teeth))

            # Диаметр окружности выступов
            if geometric_characteristic_engagement >= 1.4 and geometric_characteristic_engagement < 1.5:
                K = 0.48
            elif geometric_characteristic_engagement >= 1.5 and geometric_characteristic_engagement < 1.6:
                K = 0.532
            elif geometric_characteristic_engagement >= 1.6 and geometric_characteristic_engagement < 1.7:
                K = 0.555
            elif geometric_characteristic_engagement >= 1.7 and geometric_characteristic_engagement < 1.8:
                K = 0.575
            elif geometric_characteristic_engagement >= 1.8 and geometric_characteristic_engagement < 2.0:
                K = 0.565
            
            circle_protrusions_diam = step_chain*(K + 1/math.tan(math.radians(180)/num_teeth))

            # Радиус впадин
            hollow_radius = 0.5025*roll_diam + 0.05

            # Диаметр окружности впадин
            hollow_circle_diam = pitch_circle_diam - 2*hollow_radius 

            # Наибольшая хорда
            largest_chord = pitch_circle_diam*(math.cos(math.radians(90)/num_teeth)) - 2*hollow_radius

            # Радиус сопряжения
            fillet_radius = 0.8*roll_diam + hollow_radius

            # Половина угла впадины
            half_angle_hollow = 55 - 60/num_teeth

            # Угол сопряжения
            mating_angle = 18 - 56/num_teeth

            # Половина угла зуба
            half_angle_tooth = 17 - 64/num_teeth

            # Радиус головки зуба
            tooth_head_radius = roll_diam*(1.24*(math.cos(math.radians(half_angle_tooth))) + 0.8*(math.cos(math.radians(mating_angle))) - 1.3025) - 0.05

            # Прямой участок профиля
            straight_section_profile = roll_diam*(1.24*(math.sin(math.radians(half_angle_tooth))) - 0.8*(math.sin(math.radians(mating_angle))))

            # Расстояние от центра дуги впадины до центра дуги головки зуба
            distance_cavity_arch_tooth = 1.24*roll_diam

            # Координаты точки О1
            point_x_1 = 0.8*roll_diam*math.sin(math.radians(half_angle_hollow))
            point_y_1 = 0.8*roll_diam*math.cos(math.radians(half_angle_hollow))

            # Координаты точки О2
            point_x_2 = 1.24*roll_diam*math.cos(math.radians(180)/num_teeth)	
            point_y_2 = 1.24*roll_diam*math.sin(math.radians(180)/num_teeth)

            # Ширина зуба звездочки
            sprocket_tooth_width = 0.93*width_chain - 0.15

            # Радиус закругления зуба
            tooth_radius = 1.7*roll_diam

            # Расстояние от вершины зуба до линии центров дуг закруглений
            distance_tooth_curved_arcs = 0.8*roll_diam

            # Координаты точки A
            point_x_a = 0	
            point_y_a = hollow_circle_diam/2

            # Координаты точки O
            point_x_o = 0	
            point_y_o = pitch_circle_diam/2 

            # Координаты точки E
            point_x_e = -math.cos(math.radians(90 - half_angle_hollow))*hollow_radius
            point_y_e = hollow_circle_diam/2 + hollow_radius - math.sin(math.radians(90 - half_angle_hollow))*hollow_radius

            # Координаты точки O1
            point_x_o1 = point_x_1	
            point_y_o1 = point_y_1 + pitch_circle_diam/2

            # Координаты точки F
            point_x_f = -math.cos(math.radians(90 - mating_angle - half_angle_hollow))*fillet_radius + point_x_o1
            point_y_f = pitch_circle_diam/2 + point_y_1 - math.sin(math.radians(90 - mating_angle - half_angle_hollow))*fillet_radius

            # Координаты точки G
            point_x_g = -math.sin(math.radians(180/num_teeth + half_angle_tooth))*straight_section_profile + point_x_f
            point_y_g = math.cos(math.radians(180/num_teeth + half_angle_tooth))*straight_section_profile + point_y_f

            # Координаты точки O2
            point_x_o2 = -point_x_2
            point_y_o2 = pitch_circle_diam /2 - point_y_2

            # Координаты точки B
            point_x_b = -math.sin(math.radians(180/num_teeth))*circle_protrusions_diam/2
            point_y_b = math.cos(math.radians(180/num_teeth))*circle_protrusions_diam/2

            # Координаты точки C
            point_x_c = -math.sin(math.radians(180/num_teeth))*hollow_circle_diam/2
            point_y_c = math.cos(math.radians(180/num_teeth))*hollow_circle_diam/2

            # Получение доступа к корневому компоненту модели           
            design=app.activeProduct
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType
            rootComp = design.rootComponent

            # Создание переменной для коллекции эскизов модели
            sketches = rootComp.sketches
          
            # Создание эскиза на плоскости XY
            Sketch1 = sketches.add(rootComp.xYConstructionPlane)

            # Получение доступа к эскизным объектам типа 'окружность'            
            circles = Sketch1.sketchCurves.sketchCircles

            # Создание эскизной окружности впадин
            circles.addByCenterRadius(adsk.core.Point3D.create(0,0,0), hollow_circle_diam/20.0)

            # Создание эскизной окружно­сти отверстия
            circles.addByCenterRadius(adsk.core.Point3D.create(0,0,0), hole_diam/20.0)

            # Сохранение эскизной окружности как первого профиля
            profile1 = Sketch1.profiles.item(0) 

            extrudes = rootComp.features.extrudeFeatures
            extInput = extrudes.createInput(profile1, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

            # Выдавливание окружности на ширину зуба звездочки 
            distance = adsk.core.ValueInput.createByReal(sprocket_tooth_width/10)
            extInput.setDistanceExtent(False, distance)

            # Создание выдавливания
            baseExtrude = extrudes.add(extInput)

            # Создание эскиза на плоскости XY
            Sketch2 = sketches.add(rootComp.xYConstructionPlane)

            # Получение доступа к эскизным объектам типа 'окружность', 'дуга', 'линия'            
            circles = Sketch2.sketchCurves.sketchCircles
            arcs = Sketch2.sketchCurves.sketchArcs
            lines = Sketch2.sketchCurves.sketchLines

            # Дуга AE
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(0, point_y_o/10, 0), adsk.core.Point3D.create(0, point_y_a/10, 0),-math.pi*half_angle_hollow/180)

            # Дуга EF
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(point_x_o1/10, point_y_o1/10, 0), adsk.core.Point3D.create(point_x_e/10, point_y_e/10, 0), -math.pi*mating_angle/180)  

            # Линия FG
            lines.addByTwoPoints(adsk.core.Point3D.create(point_x_f/10, point_y_f/10, 0), adsk.core.Point3D.create(point_x_g/10, point_y_g/10, 0))

            # Дуга GK
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(point_x_o2/10, point_y_o2/10, 0), adsk.core.Point3D.create(point_x_g/10, point_y_g/10, 0), math.pi*30/180)

            # Дуга BK
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(point_x_b/10, point_y_b/10, 0), -math.pi*1/180)

            # Дуга AC
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(0, point_y_a/10, 0), math.pi*180/num_teeth/180)

            # Линия BC
            lines.addByTwoPoints(adsk.core.Point3D.create(point_x_b/10, point_y_b/10, 0), adsk.core.Point3D.create(point_x_c/10, point_y_c/10, 0))

            # Сохранение эскизной окружности как первого профиля
            profile2 = Sketch2.profiles.item(0) 

            extrudes = rootComp.features.extrudeFeatures
            extInput = extrudes.createInput(profile2, adsk.fusion.FeatureOperations.JoinFeatureOperation)

            # Выдавливание профиля зуба на ширину зуба звездочки.
            distance = adsk.core.ValueInput.createByReal(sprocket_tooth_width/10)
            extInput.setDistanceExtent(False, distance)

            # Создание выдавливания.
            toothExtrude_1 = extrudes.add(extInput)

            # Создание эскиза на плоскости XY
            Sketch3 = sketches.add(rootComp.xYConstructionPlane)

            # Получение доступа к эскизным объектам типа 'окружность', 'дуга', 'линия'            
            circles = Sketch3.sketchCurves.sketchCircles
            arcs = Sketch3.sketchCurves.sketchArcs
            lines = Sketch3.sketchCurves.sketchLines

            # Создаем зеркальный эскиз
            # Дуга -AE
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(0, point_y_o/10, 0),adsk.core.Point3D.create(0, point_y_a/10, 0), math.pi*half_angle_hollow/180)

            # Дуга -EF
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(-point_x_o1/10, point_y_o1/10, 0),adsk.core.Point3D.create(-point_x_e/10, point_y_e/10, 0), math.pi*mating_angle/180)  

            # Линия -FG
            lines.addByTwoPoints(adsk.core.Point3D.create(-point_x_f/10, point_y_f/10, 0), adsk.core.Point3D.create(-point_x_g/10, point_y_g/10, 0))

            # Дуга -GK
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(-point_x_o2/10, point_y_o2/10, 0),adsk.core.Point3D.create(-point_x_g/10, point_y_g/10, 0), -math.pi*30/180)

            # Дуга -BK
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(0,0,0),adsk.core.Point3D.create(-point_x_b/10, point_y_b/10, 0), math.pi*1/180)

            # Дуга -AC
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(0,0,0),adsk.core.Point3D.create(0, point_y_a/10, 0), -math.pi*180/num_teeth/180)

            # Линия -BC
            lines.addByTwoPoints(adsk.core.Point3D.create(-point_x_b/10, point_y_b/10, 0), adsk.core.Point3D.create(-point_x_c/10, point_y_c/10, 0))

            # Сохранение эскизной окружности как первого профиля
            profile3 = Sketch3.profiles.item(0) 

            extrudes = rootComp.features.extrudeFeatures
            extInput = extrudes.createInput(profile3, adsk.fusion.FeatureOperations.JoinFeatureOperation)

            # Выдавливание профиля зуба на ширину зуба звездочки
            distance = adsk.core.ValueInput.createByReal(sprocket_tooth_width/10)
            extInput.setDistanceExtent(False, distance)

            # Создание выдавливания
            toothExtrude_2 = extrudes.add(extInput)

            # Вызываем опирацию массив вращения
            circularPatterns = rootComp.features.circularPatternFeatures
            entities = adsk.core.ObjectCollection.create()
            entities.add(toothExtrude_1)
            entities.add(toothExtrude_2)
            cylFace = baseExtrude.sideFaces.item(0)        
            patternInput = circularPatterns.createInput(entities, cylFace)
            numTeethInput = adsk.core.ValueInput.createByString(str(num_teeth))
            patternInput.quantity = numTeethInput
            pattern = circularPatterns.add(patternInput) 

            # Создание эскиза на плоскости YZ
            Sketch4 = sketches.add(rootComp.yZConstructionPlane)

            # Получение доступа к эскизным объектам типа 'дуга', 'линия'            
            arcs = Sketch4.sketchCurves.sketchArcs
            lines = Sketch4.sketchCurves.sketchLines

            # Создание эскиза
            # Дуги
            point_1_ap = circle_protrusions_diam/2 - distance_tooth_curved_arcs
            point_2_ap = tooth_radius - sprocket_tooth_width
            point_1_ap_steps = point_1_ap + tooth_radius

            arcs.addByCenterStartSweep(adsk.core.Point3D.create(-tooth_radius/10, point_1_ap/10, 0), adsk.core.Point3D.create(0, point_1_ap/10, 0), math.pi*45/180)
            arcs.addByCenterStartSweep(adsk.core.Point3D.create(point_2_ap/10, point_1_ap/10, 0), adsk.core.Point3D.create(-sprocket_tooth_width/10, point_1_ap/10, 0), -math.pi*45/180)

            # Линии
            lines.addByTwoPoints(adsk.core.Point3D.create(0, point_1_ap/10, 0), adsk.core.Point3D.create(0, point_1_ap_steps/10, 0))
            lines.addByTwoPoints(adsk.core.Point3D.create(-sprocket_tooth_width/10, point_1_ap/10, 0), adsk.core.Point3D.create(-sprocket_tooth_width/10, point_1_ap_steps/10, 0))
            lines.addByTwoPoints(adsk.core.Point3D.create(0, point_1_ap_steps/10, 0), adsk.core.Point3D.create(-sprocket_tooth_width/10, point_1_ap_steps/10, 0))
            
            # Осевая линия
            AxisLine = lines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(-sprocket_tooth_width/10, 0, 0))

            # Сохранение эскизной окружности как профиля
            prof = Sketch4.profiles.item(0)

            # Создание операции вырез вращением
            revolves = rootComp.features.revolveFeatures
            revInput = revolves.createInput(prof, AxisLine, adsk.fusion.FeatureOperations.CutFeatureOperation)

            # Указание дистанции вращения
            # Вращение осуществить на полный оборот
            angle = adsk.core.ValueInput.createByReal(2*math.pi)
            revInput.setAngleExtent(False, angle)

            # Создание вращения
            revolves.add(revInput)

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))