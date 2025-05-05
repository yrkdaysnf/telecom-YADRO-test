import xml.etree.ElementTree as ETree
import json
from typing import Dict, List, Any


class ClassElement:
    """
    Класс для хранения информации о классе из XML.
    
    Args:
        name (str): Имя класса
        is_root (bool): Является ли корневым
        documentation (str): Документация
    """
    def __init__(self, name: str, is_root: bool, documentation: str) -> None:
        self.name: str = name
        self.is_root: bool = is_root
        self.documentation: str = documentation
        self.attributes: Dict[str, str] = {}

    def add_attribute(self, name: str, type: str) -> None:
        """
        Добавляет атрибут к классу.
        """
        self.attributes[name] = type

class Aggregation:
    """
    Класс, описывающий агрегацию между классами.

    Args:
        source (str): Исходный класс
        target (str): Целевой класс
        sourceMultiplicity (str): Мультиплицированность источника
        targetMultiplicity (str): Мультиплицированность цели
    """
    def __init__(
        self,
        source: str,
        target: str,
        sourceMultiplicity: str,
        targetMultiplicity: str
    ) -> None:
        self.source: str = source
        self.target: str = target
        self.sourceMultiplicity: str = sourceMultiplicity
        self.targetMultiplicity: str = targetMultiplicity

class ParserXML:
    """
    Класс для парсинга входного XML-файла.
    
    Args:
        path (str): Путь к XML-файлу
    """
    def __init__(self, path: str) -> None:
        self.path: str = path
        self.classes: Dict[str, ClassElement] = {}
        self.aggregations: List[Aggregation] = []

    def parse(self) -> None:
        """
        Парсит XML-файл и заполняет классы и агрегации.
        """
        root = ETree.parse(self.path).getroot()

        for element in root:
            if element.tag == 'Class':
                class_name = element.attrib['name']
                class_element = ClassElement(
                    name=class_name,
                    is_root=element.attrib['isRoot'] == 'true',
                    documentation=element.attrib.get('documentation', '')
                )
                for attr in element.findall('Attribute'):
                    class_element.add_attribute(
                        name=attr.attrib['name'],
                        type=attr.attrib['type']
                    )
                self.classes[class_name] = class_element

            elif element.tag == 'Aggregation':
                aggregation = Aggregation(
                    source=element.attrib['source'],
                    target=element.attrib['target'],
                    sourceMultiplicity=element.attrib['sourceMultiplicity'],
                    targetMultiplicity=element.attrib['targetMultiplicity']
                )
                self.aggregations.append(aggregation)

    def get_classes(self) -> Dict[str, ClassElement]:
        """
        Возвращает словарь классов.
        """
        return self.classes

    def get_aggregations(self) -> List[Aggregation]:
        """
        Возвращает список агрегаций.
        """
        return self.aggregations

class BuilderXML:
    """
    Класс для построения выходного XML-файла.
    
    Args:
        classes (Dict[str, ClassElement]): Словарь классов
        aggregations (List[Aggregation]): Список агрегаций
    """
    def __init__(self, classes: Dict[str, ClassElement], aggregations: List[Aggregation]) -> None:
        self.classes = classes
        self.aggregations = aggregations

    def build(self) -> ETree.ElementTree:
        """
        Строит XML-дерево на основе классов и агрегаций.
        """
        for class_element in self.classes.values():
            if class_element.is_root:
                root_class = class_element
                break
        else:
            raise Exception('root отсутствует')

        root_element = ETree.Element(root_class.name)
        self.add_attributes(root_element, root_class)
        self.add_nested(root_element, root_class.name)
        return ETree.ElementTree(root_element)

    def add_attributes(self, element: ETree.Element, class_element: ClassElement) -> None:
        """
        Добавляет атрибуты к XML-элементу.
        """
        for attr_name, attr_type in class_element.attributes.items():
            child = ETree.SubElement(element, attr_name)
            child.text = attr_type

    def add_nested(self, parent_element: ETree.Element, target_class_name: str) -> None:
        """
        Рекурсивно добавляет вложенные классы.
        """
        for aggregation in self.aggregations:
            if aggregation.target == target_class_name:
                source_class = self.classes[aggregation.source]
                child_element = ETree.SubElement(parent_element, source_class.name)
                self.add_attributes(child_element, source_class)
                self.add_nested(child_element, source_class.name)

class BuilderJSON:
    """
    Класс для построения JSON-файла.
    
    Args:
        classes (Dict[str, ClassElement]): Словарь классов
        aggregations (List[Aggregation]): Список агрегаций
    """
    
    def __init__(self, classes: Dict[str, ClassElement], aggregations: List[Aggregation]) -> None:
        self.classes = classes
        self.aggregations = aggregations

    def build(self) -> List[dict]:
        """
        Строит список словарей для сериализации в JSON.
        """
        nested_classes = self._get_nested_classes()
        multiplicities = self._get_multiplicities()
        json_list = []

        for class_name, class_element in self.classes.items():
            class_dict = self._build_class_dict(
                class_name=class_name,
                class_element=class_element,
                nested_classes=nested_classes,
                multiplicities=multiplicities
            )
            json_list.append(class_dict)

        return json_list

    def _get_nested_classes(self) -> Dict[str, List[str]]:
        """
        Возвращает словарь вложенных классов.
        """
        nested_classes: Dict[str, List[str]] = {}
        for aggregation in self.aggregations:
            target = aggregation.target
            source = aggregation.source
            if target not in nested_classes:
                nested_classes[target] = []
            nested_classes[target].append(source)
        return nested_classes

    def _get_multiplicities(self) -> Dict[str, Dict[str, str]]:
        """
        Возвращает словарь мультиплицирований для классов.
        """
        multiplicities: Dict[str, Dict[str, str]] = {}
        for aggregation in self.aggregations:
            source = aggregation.source
            sourceMultiplicity = aggregation.sourceMultiplicity

            if '..' in sourceMultiplicity:
                min_val, max_val = sourceMultiplicity.split('..')
            else:
                min_val = max_val = sourceMultiplicity

            multiplicities[source] = {'min': min_val, 'max': max_val}
        return multiplicities

    def _build_class_dict(
        self,
        class_name: str,
        class_element: ClassElement,
        nested_classes: Dict[str, List[str]],
        multiplicities: Dict[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Формирует словарь для одного класса.
        """
        class_dict: Dict[str, Any] = {
            'class': class_name,
            'documentation': class_element.documentation,
            'isRoot': class_element.is_root
        }

        if class_name in multiplicities:
            class_dict['min'] = multiplicities[class_name]['min']
            class_dict['max'] = multiplicities[class_name]['max']

        parameters: List[dict] = []

        for attr_name, attr_type in class_element.attributes.items():
            param = {'name': attr_name, 'type': attr_type}
            parameters.append(param)

        if class_name in nested_classes:
            for nested_class_name in nested_classes[class_name]:
                param = {'name': nested_class_name, 'type': 'class'}
                parameters.append(param)

        class_dict['parameters'] = parameters
        return class_dict
    
class Delta:
    """
    Класс для хранения дельты между двумя конфигами.

    Args:
        additions (List[Dict[str, Any]]): Новые параметры
        deletions (List[str]): Удалённые параметры
        updates (List[Dict[str, Any]]): Изменённые параметры
    """
    def __init__(
        self,
        additions: List[Dict[str, Any]],
        deletions: List[str],
        updates: List[Dict[str, Any]]
    ) -> None:
        self.additions = additions
        self.deletions = deletions
        self.updates = updates

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует дельту в словарь для сериализации в JSON.
        """
        return {
            "additions": self.additions,
            "deletions": self.deletions,
            "updates": self.updates
        }

    @staticmethod
    def from_configs(
        old_config: Dict[str, Any],
        new_config: Dict[str, Any]
    ) -> 'Delta':
        """
        Генерирует дельту между двумя конфигами.
        """
        additions = []
        deletions = []
        updates = []

        for key in new_config:
            if key not in old_config:
                additions.append({"key": key, "value": new_config[key]})
            elif old_config[key] != new_config[key]:
                updates.append({
                    "key": key,
                    "from": old_config[key],
                    "to": new_config[key]
                })
        for key in old_config:
            if key not in new_config:
                deletions.append(key)
        return Delta(additions, deletions, updates)


class ConfigPatcher:
    """
    Класс для применения дельты к конфигу.

    Args:
        base_config (Dict[str, Any]): Исходный конфиг
        delta (Delta): Дельта изменений
    """
    def __init__(self, base_config: Dict[str, Any], delta: Delta) -> None:
        self.base_config = base_config
        self.delta = delta

    def apply(self) -> Dict[str, Any]:
        """
        Применяет дельту к исходному конфигу.
        """
        result = self.base_config.copy()
        # Удаления
        for key in self.delta.deletions:
            result.pop(key, None)
        # Обновления
        for upd in self.delta.updates:
            result[upd["key"]] = upd["to"]
        # Добавления
        for add in self.delta.additions:
            result[add["key"]] = add["value"]
        return result


def load_json(path: str) -> Dict[str, Any]:
    """
    Загружает JSON-файл в словарь.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: str, data: Any) -> None:
    """
    Сохраняет данные в JSON-файл.
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # Парсинг входного xml
    parser = ParserXML('input\\impulse_test_input.xml')
    parser.parse()

    # Тут генерируется и записывается config.xml на основе парсинга входного xml
    xml_builder = BuilderXML(
        classes=parser.get_classes(),
        aggregations=parser.get_aggregations()
    )
    xml_tree = xml_builder.build()
    ETree.indent(xml_tree, '\t')
    xml_tree.write('out\\config.xml')

    # Тут генерируется и записывается meta.json на основе парсинга входного xml
    json_builder = BuilderJSON(
        classes=parser.get_classes(),
        aggregations=parser.get_aggregations()
    )
    json_data = json_builder.build()
    save_json('out\\meta.json', json_data)

    # Загрузка конфигов
    config = load_json('input\\config.json')
    patched_config = load_json('input\\patched_config.json')

    # Генерация дельты
    delta = Delta.from_configs(config, patched_config)
    save_json('out\\delta.json', delta.to_dict())

    # Применение дельты
    patcher = ConfigPatcher(config, delta)
    res_patched = patcher.apply()
    save_json('out\\res_patched_config.json', res_patched)