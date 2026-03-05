"""
NeuralSite Knowledge Graph Client
Neo4j客户端 - 道路工程知识图谱管理
"""

from typing import Optional, List, Dict, Any
from neo4j import GraphDatabase, Driver
import logging

logger = logging.getLogger(__name__)


class KnowledgeGraphClient:
    """Neo4j知识图谱客户端"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", 
                 password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver: Optional[Driver] = None
    
    def connect(self) -> bool:
        """连接到Neo4j数据库"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # 测试连接
            with self._driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> Optional[str]:
        """创建节点"""
        if not self._driver:
            return None
        
        with self._driver.session() as session:
            query = f"CREATE (n:{label} $props) RETURN id(n) as node_id"
            result = session.run(query, props=properties)
            record = result.single()
            return str(record["node_id"]) if record else None
    
    def create_relationship(self, 
                           start_node_id: str, 
                           end_node_id: str, 
                           rel_type: str, 
                           properties: Optional[Dict[str, Any]] = None) -> bool:
        """创建关系"""
        if not self._driver:
            return False
        
        with self._driver.session() as session:
            props_str = ", $props" if properties else ""
            query = f"""
            MATCH (a), (b)
            WHERE id(a) = $start_id AND id(b) = $end_id
            CREATE (a)-[r:{rel_type}{props_str}]->(b)
            RETURN r
            """
            params = {"start_id": int(start_node_id), "end_id": int(end_node_id)}
            if properties:
                params["props"] = properties
            result = session.run(query, **params)
            return result.single() is not None
    
    def find_node(self, label: str, property_key: str, property_value: Any) -> Optional[Dict[str, Any]]:
        """查找节点"""
        if not self._driver:
            return None
        
        with self._driver.session() as session:
            query = f"MATCH (n:{label} {{{property_key}: $value}}) RETURN n, id(n) as node_id"
            result = session.run(query, value=property_value)
            record = result.single()
            if record:
                return {
                    "id": str(record["node_id"]),
                    "properties": dict(record["n"])
                }
            return None
    
    def find_nodes(self, label: str) -> List[Dict[str, Any]]:
        """查找所有指定类型的节点"""
        if not self._driver:
            return []
        
        with self._driver.session() as session:
            query = f"MATCH (n:{label}) RETURN n, id(n) as node_id"
            results = session.run(query)
            nodes = []
            for record in results:
                nodes.append({
                    "id": str(record["node_id"]),
                    "properties": dict(record["n"])
                })
            return nodes
    
    def get_relationships(self, node_id: str, direction: str = "outgoing") -> List[Dict[str, Any]]:
        """获取节点的关系"""
        if not self._driver:
            return []
        
        with self._driver.session() as session:
            if direction == "outgoing":
                query = """
                MATCH (a)-[r]->(b)
                WHERE id(a) = $node_id
                RETURN id(a) as start_id, id(b) as end_id, type(r) as rel_type, r as props
                """
            else:
                query = """
                MATCH (a)<-[r]-(b)
                WHERE id(a) = $node_id
                RETURN id(a) as start_id, id(b) as end_id, type(r) as rel_type, r as props
                """
            result = session.run(query, node_id=int(node_id))
            rels = []
            for record in result:
                rels.append({
                    "start_id": str(record["start_id"]),
                    "end_id": str(record["end_id"]),
                    "type": record["rel_type"],
                    "properties": dict(record["props"]) if record["props"] else {}
                })
            return rels
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        if not self._driver:
            return []
        
        with self._driver.session() as session:
            result = session.run(query, **(params or {}))
            return [dict(record) for record in result]
    
    def delete_all(self) -> bool:
        """删除所有节点和关系（谨慎使用）"""
        if not self._driver:
            return False
        
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            return True
    
    def get_stats(self) -> Dict[str, int]:
        """获取图谱统计信息"""
        if not self._driver:
            return {}
        
        with self._driver.session() as session:
            # 节点数量统计
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
            
            # 关系数量统计
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
            
            # 各类型节点统计
            labels = session.run("CALL db.labels()").to_list()
            label_counts = {}
            for label in labels:
                count = session.run(f"MATCH (n:{label}) RETURN count(n) as count").single()["count"]
                label_counts[label] = count
            
            return {
                "nodes": node_count,
                "relationships": rel_count,
                "by_label": label_counts
            }


# 全局客户端实例
_client: Optional[KnowledgeGraphClient] = None


def get_graph_client() -> KnowledgeGraphClient:
    """获取全局知识图谱客户端实例"""
    global _client
    if _client is None:
        _client = KnowledgeGraphClient()
    return _client


def init_graph_client(uri: str = "bolt://localhost:7687",
                      user: str = "neo4j", 
                      password: str = "password") -> KnowledgeGraphClient:
    """初始化并返回知识图谱客户端"""
    global _client
    _client = KnowledgeGraphClient(uri, user, password)
    _client.connect()
    return _client
