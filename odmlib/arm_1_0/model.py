import odmlib.define_2_1.model as DEF
import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS

NS.NamespaceRegistry(prefix="arm", uri="http://www.cdisc.org/ns/arm/v1.0")

class Description(DEF.Description):
    TranslatedText = DEF.Description.TranslatedText

class WhereClauseRef(DEF.WhereClauseRef):
    namespace = "def"
    WhereClauseOID = DEF.WhereClauseRef.WhereClauseOID

class PDFPageRef(DEF.PDFPageRef):
    namespace = "def"
    Type = DEF.PDFPageRef.Type
    PageRefs = DEF.PDFPageRef.PageRefs
    FirstPage = DEF.PDFPageRef.FirstPage
    LastPage = DEF.PDFPageRef.LastPage
    Title = DEF.PDFPageRef.Title

class DocumentRef(DEF.DocumentRef):
    namespace = "def"
    leafID = DEF.DocumentRef.leafID
    PDFPageRef = T.ODMListObject(element_class=PDFPageRef)

class Documentation(OE.ODMElement):
    namespace = "arm"
    Description = T.ODMObject(element_class=Description)
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")

class Code(OE.ODMElement):
    namespace = "arm"
    _content = T.String(required=False)

class ProgrammingCode(OE.ODMElement):
    namespace = "arm"
    Context = T.String
    Code = T.ODMObject(element_class=Code, namespace="arm")
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")

class AnalysisVariable(OE.ODMElement):
    namespace = "arm"
    ItemOID = T.OIDRef(required=True)

class AnalysisDataset(OE.ODMElement):
    namespace = "arm"
    ItemGroupOID = T.OIDRef(required=True)
    WhereClauseRef = T.ODMObject(element_class=WhereClauseRef, namespace="def")
    AnalysisVariable = T.ODMListObject(element_class=AnalysisVariable, namespace="arm")

class AnalysisDatasets(OE.ODMElement):
    namespace = "arm"
    CommentOID = T.OIDRef(namespace="def")
    AnalysisDataset = T.ODMListObject(element_class=AnalysisDataset, namespace="arm")

    def __len__(self):
        return len(self.AnalysisDataset)

    def __getitem__(self, position):
        return self.AnalysisDataset[position]

    def __iter__(self):
        return iter(self.AnalysisDataset)

class AnalysisResult(OE.ODMElement):
    namespace = "arm"
    OID = T.OID(required=True)
    ParameterOID = T.OIDRef(required=False)
    AnalysisReason = T.ExtendedValidValues(required=True, valid_values=["SPECIFIED IN PROTOCOL", "SPECIFIED IN SAP",
                                                                        "DATA DRIVEN", "REQUESTED BY REGULATORY AGENCY"])
    AnalysisPurpose = T.ExtendedValidValues(required=True, valid_values=["PRIMARY OUTCOME MEASURE", "SECONDARY OUTCOME MEASURE",
                                                                         "EXPLORATORY OUTCOME MEASURE"])
    Description = T.ODMObject(element_class=Description)
    Documentation = T.ODMObject(element_class=Documentation, namespace="arm")
    ProgrammingCode = T.ODMObject(element_class=ProgrammingCode, namespace="arm")
    AnalysisDatasets = T.ODMObject(element_class=AnalysisDatasets, namespace="arm")

class ResultDisplay(OE.ODMElement):
    namespace = "arm"
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")
    AnalysisResult = T.ODMListObject(element_class=AnalysisResult, required=True, namespace="arm")

    def __len__(self):
        return len(self.AnalysisResult)

    def __getitem__(self, position):
        return self.AnalysisResult[position]

    def __iter__(self):
        return iter(self.AnalysisResult)

class AnalysisResultDisplays(OE.ODMElement):
    namespace = "arm"
    ResultDisplay = T.ODMListObject(element_class=ResultDisplay, required=True, namespace="arm")

    def __len__(self):
        return len(self.ResultDisplay)

    def __getitem__(self, position):
        return self.ResultDisplay[position]

    def __iter__(self):
        return iter(self.ResultDisplay)

class TranslatedText(DEF.TranslatedText):
    lang = DEF.TranslatedText.lang
    _content = DEF.TranslatedText._content

class Alias(DEF.Alias):
    Context = DEF.Alias.Context
    Name = DEF.Alias.Name

class StudyDescription(DEF.StudyDescription):
    _content = DEF.StudyDescription._content

class ProtocolName(DEF.ProtocolName):
    _content = DEF.ProtocolName._content

class StudyName(DEF.StudyName):
    _content = DEF.StudyName._content

class GlobalVariables(DEF.GlobalVariables):
    StudyName = DEF.GlobalVariables.StudyName
    StudyDescription = DEF.GlobalVariables.StudyDescription
    ProtocolName = DEF.GlobalVariables.ProtocolName

class ItemRef(DEF.ItemRef):
    ItemOID =DEF.ItemRef.ItemOID
    OrderNumber = DEF.ItemRef.OrderNumber
    Mandatory = DEF.ItemRef.Mandatory
    KeySequence = DEF.ItemRef.KeySequence
    MethodOID = DEF.ItemRef.MethodOID
    Role = DEF.ItemRef.Role
    RoleCodeListOID = DEF.ItemRef.RoleCodeListOID
    IsNonStandard = DEF.ItemRef.IsNonStandard
    HasNoData = DEF.ItemRef.HasNoData
    WhereClauseRef = DEF.ItemRef.WhereClauseRef

class title(DEF.title):
    namespace = "def"
    _content = DEF.title._content

class leaf(DEF.leaf):
    namespace = "def"
    ID = DEF.leaf.ID
    href = DEF.leaf.href
    title = DEF.leaf.title

class SubClass(DEF.SubClass):
    namespace = "def"
    Name = DEF.SubClass.Name
    ParentClass = DEF.SubClass.ParentClass

class Class(DEF.Class):
    namespace = "def"
    Name = DEF.Class.Name
    SubClass = DEF.Class.SubClass

class ItemGroupDef(DEF.ItemGroupDef):
    OID = DEF.ItemGroupDef.OID
    Name = DEF.ItemGroupDef.Name
    Repeating = DEF.ItemGroupDef.Repeating
    IsReferenceData = DEF.ItemGroupDef.IsReferenceData
    SASDatasetName = DEF.ItemGroupDef.SASDatasetName
    Domain = DEF.ItemGroupDef.Domain
    Purpose = DEF.ItemGroupDef.Purpose
    Structure = DEF.ItemGroupDef.Structure
    ArchiveLocationID = DEF.ItemGroupDef.ArchiveLocationID
    CommentOID = DEF.ItemGroupDef.CommentOID
    IsNonStandard = DEF.ItemGroupDef.IsNonStandard
    StandardOID = DEF.ItemGroupDef.StandardOID
    HasNoData = DEF.ItemGroupDef.HasNoData
    Description = DEF.ItemGroupDef.Description
    ItemRef = DEF.ItemGroupDef.ItemRef
    Alias = DEF.ItemGroupDef.Alias
    Class = DEF.ItemGroupDef.Class
    leaf = DEF.ItemGroupDef.leaf

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)

class CheckValue(DEF.CheckValue):
    _content = T.String(required=False)

class FormalExpression(DEF.FormalExpression):
    Context = DEF.FormalExpression.Context
    _content = DEF.FormalExpression._content

class RangeCheck(DEF.RangeCheck):
    Comparator = DEF.RangeCheck.Comparator
    SoftHard = DEF.RangeCheck.SoftHard
    ItemOID = DEF.RangeCheck.ItemOID
    CheckValue = DEF.RangeCheck.CheckValue

class CodeListRef(DEF.CodeListRef):
    CodeListOID = DEF.CodeListRef.CodeListOID

class ValueListRef(DEF.ValueListRef):
    namespace = "def"
    ValueListOID = DEF.ValueListRef.ValueListOID

class PDFPageRef(DEF.PDFPageRef):
    namespace = "def"
    Type = DEF.PDFPageRef.Type
    PageRefs = DEF.PDFPageRef.PageRefs
    FirstPage = DEF.PDFPageRef.FirstPage
    LastPage = DEF.PDFPageRef.LastPage
    Title = DEF.PDFPageRef.Title

class DocumentRef(DEF.DocumentRef):
    namespace = "def"
    leafID = DEF.DocumentRef.leafID
    PDFPageRef = DEF.DocumentRef.PDFPageRef

class Origin(DEF.Origin):
    namespace = "def"
    Type = DEF.Origin.Type
    Source = DEF.Origin.Source
    Description = DEF.Origin.Description
    DocumentRef = DEF.Origin.DocumentRef

class ItemDef(DEF.ItemDef):
    OID = DEF.ItemDef.OID
    Name = DEF.ItemDef.Name
    DataType = DEF.ItemDef.DataType
    Length = DEF.ItemDef.Length
    SignificantDigits = DEF.ItemDef.SignificantDigits
    SASFieldName = DEF.ItemDef.SASFieldName
    DisplayFormat = DEF.ItemDef.DisplayFormat
    CommentOID = DEF.ItemDef.CommentOID
    Description = DEF.ItemDef.Description
    CodeListRef = DEF.ItemDef.CodeListRef
    Origin = DEF.ItemDef.Origin
    ValueListRef = DEF.ItemDef.ValueListRef
    Alias = DEF.ItemDef.Alias

class Decode(DEF.Decode):
    TranslatedText = DEF.Decode.TranslatedText

class CodeListItem(DEF.CodeListItem):
    CodedValue = DEF.CodeListItem.CodedValue
    Rank = DEF.CodeListItem.Rank
    OrderNumber = DEF.CodeListItem.OrderNumber
    ExtendedValue = DEF.CodeListItem.ExtendedValue
    Description = DEF.CodeList.Description
    Decode = DEF.CodeListItem.Decode
    Alias = DEF.CodeListItem.Alias

class EnumeratedItem(DEF.EnumeratedItem):
    CodedValue = DEF.EnumeratedItem.CodedValue
    Rank = DEF.EnumeratedItem.Rank
    OrderNumber = DEF.EnumeratedItem.OrderNumber
    ExtendedValue = DEF.EnumeratedItem.ExtendedValue
    Description = DEF.CodeList.Description
    Alias = DEF.EnumeratedItem.Alias

class ExternalCodeList(DEF.ExternalCodeList):
    Dictionary = DEF.ExternalCodeList.Dictionary
    Version = DEF.ExternalCodeList.Version
    ref = DEF.ExternalCodeList.ref
    href = DEF.ExternalCodeList.href

class CodeList(DEF.CodeList):
    OID = DEF.CodeList.OID
    Name = DEF.CodeList.Name
    DataType = DEF.CodeList.DataType
    IsNonStandard = DEF.CodeList.IsNonStandard
    StandardOID = DEF.CodeList.StandardOID
    SASFormatName = DEF.CodeList.SASFormatName
    CommentOID = DEF.CodeList.CommentOID
    Description = DEF.CodeList.Description
    CodeListItem = DEF.CodeList.CodeListItem
    EnumeratedItem = DEF.CodeList.EnumeratedItem
    ExternalCodeList = DEF.CodeList.ExternalCodeList
    Alias = DEF.CodeList.Alias

class MethodDef(DEF.MethodDef):
    OID = DEF.MethodDef.OID
    Name = DEF.MethodDef.Name
    Type = DEF.MethodDef.Type
    Description = DEF.MethodDef.Description
    FormalExpression = DEF.MethodDef.FormalExpression
    DocumentRef = DEF.MethodDef.DocumentRef

class AnnotatedCRF(DEF.AnnotatedCRF):
    namespace = "def"
    DocumentRef = DEF.AnnotatedCRF.DocumentRef

class SupplementalDoc(DEF.SupplementalDoc):
    namespace = "def"
    DocumentRef = DEF.SupplementalDoc.DocumentRef

class WhereClauseDef(DEF.WhereClauseDef):
    namespace = "def"
    OID = DEF.WhereClauseDef.OID
    CommentOID = DEF.WhereClauseDef.CommentOID
    RangeCheck = DEF.WhereClauseDef.RangeCheck

class ValueListDef(DEF.ValueListDef):
    namespace = "def"
    OID = DEF.ValueListDef.OID
    Description = DEF.ValueListDef.Description
    ItemRef = DEF.ValueListDef.ItemRef

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)

class CommentDef(DEF.CommentDef):
    namespace = "def"
    OID = DEF.CommentDef.OID
    Description = DEF.CommentDef.Description
    DocumentRef = DEF.CommentDef.DocumentRef

class Standard(DEF.Standard):
    namespace = "def"
    OID = DEF.Standard.OID
    Name = DEF.Standard.Name
    Type = DEF.Standard.Type
    PublishingSet = DEF.Standard.PublishingSet
    Version = DEF.Standard.Version
    Status = DEF.Standard.Status
    CommentOID = DEF.Standard.CommentOID

class Standards(DEF.Standards):
    namespace = "def"
    Standard = DEF.Standards.Standard

    def __len__(self):
        return len(self.Standard)

    def __getitem__(self, position):
        return self.Standard[position]

    def __iter__(self):
        return iter(self.Standard)

class MetaDataVersion(DEF.MetaDataVersion):
    OID = DEF.MetaDataVersion.OID
    Name = DEF.MetaDataVersion.Name
    Description = DEF.MetaDataVersion.Description
    DefineVersion = DEF.MetaDataVersion.DefineVersion
    CommentOID = DEF.MetaDataVersion.CommentOID
    Standards = DEF.MetaDataVersion.Standards
    AnnotatedCRF = DEF.MetaDataVersion.AnnotatedCRF
    SupplementalDoc = DEF.MetaDataVersion.SupplementalDoc
    ValueListDef = DEF.MetaDataVersion.ValueListDef
    WhereClauseDef = DEF.MetaDataVersion.WhereClauseDef
    ItemGroupDef = DEF.MetaDataVersion.ItemGroupDef
    ItemDef = DEF.MetaDataVersion.ItemDef
    CodeList = DEF.MetaDataVersion.CodeList
    MethodDef = DEF.MetaDataVersion.MethodDef
    CommentDef = DEF.MetaDataVersion.CommentDef
    leaf = DEF.MetaDataVersion.leaf
    AnalysisResultDisplays = T.ODMObject(element_class=AnalysisResultDisplays, namespace="arm")

class Study(DEF.Study):
    OID = DEF.Study.OID
    GlobalVariables = DEF.Study.GlobalVariables
    MetaDataVersion = T.ODMObject(required=True, element_class=MetaDataVersion)

class ODM(DEF.ODM):
    FileType = DEF.ODM.FileType
    FileOID = DEF.ODM.FileOID
    CreationDateTime = DEF.ODM.CreationDateTime
    AsOfDateTime = DEF.ODM.AsOfDateTime
    ODMVersion = DEF.ODM.ODMVersion
    Originator = DEF.ODM.Originator
    SourceSystem = DEF.ODM.SourceSystem
    SourceSystemVersion = DEF.ODM.SourceSystemVersion
    schemaLocation = DEF.ODM.schemaLocation
    Context = DEF.ODM.Context
    ID = DEF.ODM.ID
    Study = T.ODMObject(required=True, element_class=Study)