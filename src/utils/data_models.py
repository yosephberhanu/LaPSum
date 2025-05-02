from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class UMLParameter(BaseModel):
    name: Optional[str] = Field(None, description="The name of the method parameter")
    type: Optional[str] = Field(None, description="The data type of the method parameter")

class UMLProperty(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the property")
    # domId: Optional[str] = Field(None, description="Frontend DOM element ID for UI representation")
    name: Optional[str] = Field(None, description="The internal name of the property")
    # displayName: Optional[str] = Field(None, description="The user-friendly name shown in diagrams")
    summary: Optional[str] = Field(None, description="Short description or documentation for the property")
    selected: Optional[bool] = Field(None, description="Indicates if the property is currently selected in the UI")
    dataType: Optional[str] = Field(None, description="The data type of the property (e.g., int, String)")
    visibility: Optional[Literal["public", "private", "protected", "package"]] = Field(None, description="Access level of the property")
    isStatic: Optional[bool] = Field(None, description="Indicates whether the property is static")
    isFinal: Optional[bool] = Field(None, description="Indicates whether the property is a constant (final)")
    annotations: Optional[List[str]] = Field(None, description="Annotations or decorators applied to the property")
    sourceLine: Optional[str] = Field(None, description="Line number in the source file where the property is defined")

class UMLMethod(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the method")
    # domId: Optional[str] = Field(None, description="Frontend DOM element ID for the method")
    name: Optional[str] = Field(None, description="Internal method name")
    # displayName: Optional[str] = Field(None, description="User-friendly method name for display")
    summary: Optional[str] = Field(None, description="Short documentation or summary of the method")
    selected: Optional[bool] = Field(None, description="Selection state in the UI")
    returnType: Optional[str] = Field(None, description="Return type of the method")
    parameters: Optional[List[UMLParameter]] = Field(None, description="List of method parameters")
    visibility: Optional[Literal["public", "private", "protected", "package"]] = Field(None, description="Access level of the method")
    annotations: Optional[List[str]] = Field(None, description="List of annotations applied to the method")
    isStatic: Optional[bool] = Field(None, description="True if the method is static")
    isAbstract: Optional[bool] = Field(None, description="True if the method is abstract")
    startingLine: Optional[int] = Field(None, description="Line number where the method starts")
    endingLine: Optional[int] = Field(None, description="Line number where the method ends")

class UMLClass(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the class")
    # domId: Optional[str] = Field(None, description="DOM element ID for the class in UI")
    name: Optional[str] = Field(None, description="Internal class name")
    # displayName: Optional[str] = Field(None, description="User-friendly name shown in the diagram")
    summary: Optional[str] = Field(None, description="Short description or docstring for the class")
    selected: Optional[bool] = Field(None, description="Indicates selection state in the UI")
    package: Optional[str] = Field(None, description="Package or namespace the class belongs to")
    files: Optional[List[str]] = Field(None, description="List of source files where the class is defined")
    annotations: Optional[List[str]] = Field(None, description="Class-level annotations")
    properties: Optional[List[UMLProperty]] = Field(None, description="List of class properties")
    methods: Optional[List[UMLMethod]] = Field(None, description="List of class methods")
    isAbstract: Optional[bool] = Field(None, description="True if the class is abstract")
    isInterface: Optional[bool] = Field(None, description="True if the class is an interface")

class UMLRelationship(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the relationship")
    # domId: Optional[str] = Field(None, description="DOM element ID for visual linking")
    name: Optional[str] = Field(None, description="Name or label of the relationship")
    # displayName: Optional[str] = Field(None, description="Display name for UI")
    source: Optional[str] = Field(None, description="Source component of the relationship")
    target: Optional[str] = Field(None, description="target component for the relationship")
    type: Optional[Literal["inheritance", "interface_implementation", "association", "aggregation", "composition", "dependency"]] = Field(None, description="Type of the relationship")
    # multiplicity: Optional[str] = Field(None, description="multiplicity of the relationship")

class UMLClassDiagram(BaseModel):
    # id: Optional[str] = Field(None, description="Unique identifier for the class diagram")
    # language: Optional[str] = Field(None, description="Programming language of the diagram (e.g., Java, Python)")
    # note: Optional[str] = Field(None, description="General notes or comments about the diagram")
    # name: Optional[str] = Field(None, description="Name of the UML diagram")
    type: Optional[Literal["class", "object", "component", "deployment", "package", "composite"]] = Field(None, description="Type of UML diagram")
    classes: Optional[List[UMLClass]] = Field(default_factory=list, description="List of classes in the diagram")
    relationships: Optional[List[UMLRelationship]] = Field(default_factory=list, description="List of relationships between classes")


# from langchain.output_parsers import StructuredOutputParser

# parser = StructuredOutputParser.from_pydantic(UMLClassDiagram)