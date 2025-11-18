"""Extractor registry for managing and discovering extractors."""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExtractorRegistry:
    """
    Singleton registry for managing all extractors.
    
    Extractors register themselves on initialization, making it easy
    to add new extractors without modifying the service code.
    """
    
    _instance: Optional['ExtractorRegistry'] = None
    _extractors: Dict[str, 'BaseExtractor'] = {}
    
    def __new__(cls):
        """Ensure only one registry instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._extractors = {}
        return cls._instance
    
    def register(self, extractor: 'BaseExtractor') -> None:
        """
        Register an extractor.
        
        Args:
            extractor: Extractor instance to register
        """
        name = extractor.name
        
        if name in self._extractors:
            logger.warning(
                f"Extractor '{name}' already registered. Overwriting with "
                f"new instance (table: {extractor.table_name})"
            )
        
        self._extractors[name] = extractor
        logger.info(
            f"Registered extractor: {name} -> table: {extractor.table_name} "
            f"(version: {extractor.version})"
        )
    
    def get(self, name: str) -> Optional['BaseExtractor']:
        """
        Get an extractor by name.
        
        Args:
            name: Extractor name
            
        Returns:
            Extractor instance or None if not found
        """
        return self._extractors.get(name)
    
    def get_by_table(self, table_name: str) -> Optional['BaseExtractor']:
        """
        Get an extractor by its target table name.
        
        Args:
            table_name: Database table name
            
        Returns:
            Extractor instance or None if not found
        """
        for extractor in self._extractors.values():
            if extractor.table_name == table_name:
                return extractor
        return None
    
    def list_all(self) -> Dict[str, 'BaseExtractor']:
        """
        Get all registered extractors.
        
        Returns:
            Dictionary mapping extractor names to instances
        """
        return self._extractors.copy()
    
    def list_names(self) -> List[str]:
        """
        List all registered extractor names.
        
        Returns:
            List of extractor names
        """
        return list(self._extractors.keys())
    
    def unregister(self, name: str) -> bool:
        """
        Unregister an extractor.
        
        Args:
            name: Extractor name
            
        Returns:
            True if extractor was removed, False if not found
        """
        if name in self._extractors:
            del self._extractors[name]
            logger.info(f"Unregistered extractor: {name}")
            return True
        return False
    
    def __len__(self) -> int:
        """Get number of registered extractors."""
        return len(self._extractors)
    
    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"<ExtractorRegistry(extractors={len(self)})>"


# Global singleton instance
registry = ExtractorRegistry()

